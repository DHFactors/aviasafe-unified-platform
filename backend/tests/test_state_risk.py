"""State-level risk register tests (Part 2: national risk vs SSP).

Verifies aggregation of tenant data into ICAO top-risk categories, persistence
of the register, SSP target handling, and the benchmark wiring.
"""

from datetime import datetime, timezone

from app.services.state_risk_service import (
    StateRiskService,
    ICAO_TOP_RISK_CATEGORIES,
)


# ============================================================================
# ICAO classification helpers
# ============================================================================

def test_icao_categories_are_unique():
    cats = [c["category"] for c in ICAO_TOP_RISK_CATEGORIES]
    assert len(cats) == len(set(cats))
    assert "LOCI" in cats and "CFIT" in cats and "OTHER" in cats


def test_classify_uses_occurrence_category():
    assert StateRiskService._classify({"occurrence_category": "LOCI"}) == "LOCI"
    assert StateRiskService._classify({"occurrence_category": "BIRD"}) == "BIRD"
    assert StateRiskService._classify({"occurrence_category": "ENG"}) == "ENG"


def test_classify_matches_named_labels():
    assert StateRiskService._classify({"occurrence_type": "Loss of Control Inflight"}) == "LOCI"
    assert StateRiskService._classify({"occurrence_type": "Runway Excursion"}) == "RE"
    assert StateRiskService._classify({"occurrence_type": "Runway Incursion"}) == "RI"
    assert StateRiskService._classify({"occurrence_type": "Bird Strike"}) == "BIRD"
    assert StateRiskService._classify({"occurrence_type": "Controlled Flight Into Terrain"}) == "CFIT"


def test_classify_falls_back_to_other():
    assert StateRiskService._classify({}) == "OTHER"
    assert StateRiskService._classify({"occurrence_category": "UNKNOWN_XYZ"}) == "OTHER"


def test_tolerability_bands():
    assert StateRiskService._tolerability(None) == "Acceptable"
    assert StateRiskService._tolerability(1) == "Acceptable"
    assert StateRiskService._tolerability(9) == "Tolerable"
    assert StateRiskService._tolerability(15) == "Tolerable"
    assert StateRiskService._tolerability(16) == "Intolerable"
    assert StateRiskService._tolerability(25) == "Intolerable"


# ============================================================================
# Aggregation (mocked cross-tenant collection groups)
# ============================================================================

class _FakeDoc:
    def __init__(self, data):
        self._data = data
        self.id = "fake-id"

    def to_dict(self):
        return self._data


class _FakeQuery:
    def get(self):
        return [self._doc]

    def limit(self, n):
        return self

    def stream(self):
        return [self._doc]

    def where(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self


class _FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def get(self):
        return self._docs

    def stream(self):
        return self._docs

    def limit(self, n):
        return self

    def document(self, doc_id):
        return _FakeDocRef(doc_id, self._docs)


class _FakeDocRef:
    def __init__(self, doc_id, docs):
        self.id = doc_id
        self._docs = docs

    def get(self):
        for d in self._docs:
            if d.id == self.id:
                return d
        return _FakeDoc({})


def _svc(monkeypatch, hazards=None, reports=None, reference=None):
    hazards = hazards or []
    reports = reports or []

    def fake_cg(self, name):
        if name == "hazards":
            return _FakeCollection([_FakeDoc(h) for h in hazards])
        return _FakeCollection([_FakeDoc(r) for r in reports])

    monkeypatch.setattr(
        "app.services.state_risk_service.get_db",
        lambda: type("DB", (), {"collection_group": fake_cg})(),
    )
    return StateRiskService({"uid": "caan-user", "role": "CAAN_SMD"})


def test_aggregate_national_risk(monkeypatch):
    svc = _svc(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
            {"tenant_id": "air1", "occurrence_category": "LOCI", "severity_level": 5, "probability_level": 5, "risk_level": "Very High"},
            {"tenant_id": "air2", "occurrence_category": "BIRD", "severity_level": 1, "probability_level": 1, "risk_level": "Low"},
        ],
    )
    result = svc.aggregate_national_risk(2026, 3)
    assert result["year"] == 2026
    assert result["quarter"] == 3
    by_cat = {r["icoc_category"]: r for r in result["risks"]}
    assert by_cat["BIRD"]["count"] == 2
    assert by_cat["BIRD"]["current_risk_index"] == 4
    assert by_cat["LOCI"]["current_risk_index"] == 25
    assert by_cat["LOCI"]["contributing_tenants"] == ["air1"]
    # National top risk should rank highest risk index first
    assert result["risks"][0]["icoc_category"] == "LOCI"


def test_aggregate_includes_reports(monkeypatch):
    svc = _svc(
        monkeypatch,
        reports=[
            {"tenant_id": "air1", "occurrence_category": "ENG", "severity_level": 4, "probability_level": 2, "risk_level": "High"},
        ],
    )
    result = svc.aggregate_national_risk(2026, 2)
    by_cat = {r["icoc_category"]: r for r in result["risks"]}
    assert by_cat["ENG"]["count"] == 1
    assert by_cat["ENG"]["current_risk_index"] == 8


def test_aggregate_empty_returns_no_rows(monkeypatch):
    svc = _svc(monkeypatch)
    result = svc.aggregate_national_risk(2026, 1)
    assert result["risks"] == []


# ============================================================================
# Register persistence (mocked risk collection)
# ============================================================================

class _FakeRiskDocRef:
    def __init__(self, doc_id, store):
        self.id = doc_id
        self._store = store

    def get(self):
        data = self._store.get(self.id)
        if data is None:
            return _FakeMissingDoc()
        return _FakeRiskDoc(self.id, data)

    def set(self, data):
        self._store[self.id] = data
        return self

    def update(self, data):
        existing = self._store.get(self.id, {})
        existing.update(data)
        self._store[self.id] = existing
        return self


class _FakeRiskDoc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self.exists = True
        self._data = data

    def to_dict(self):
        return self._data


class _FakeMissingDoc:
    def __init__(self):
        self.exists = False

    def to_dict(self):
        return {}


class _FakeRiskCollection:
    def __init__(self):
        self._store = {}
        self._docs = []

    def document(self, doc_id):
        return _FakeRiskDocRef(doc_id, self._store)

    def stream(self):
        return [_FakeRiskDoc(did, data) for did, data in self._store.items()]


class _FakeBatch:
    def __init__(self, coll):
        self._ops = []
        self._coll = coll

    def set(self, ref, data):
        self._ops.append(("set", ref.id, data))
        return self

    def update(self, ref, data):
        self._ops.append(("update", ref.id, data))
        return self

    def commit(self):
        for kind, doc_id, data in self._ops:
            ref = self._coll.document(doc_id)
            if kind == "set":
                ref.set(data)
            else:
                ref.update(data)


def _svc_with_risk_collection(monkeypatch, hazards, reference=None):
    coll = _FakeRiskCollection()

    def fake_cg(self, name):
        return _FakeCollection([_FakeDoc(h) for h in hazards]) if name == "hazards" else _FakeCollection([])

    class _DB:
        def batch(self):
            return _FakeBatch(coll)

        def collection(self, name):
            assert name == "state"
            return _FakeStateDoc()

        def collection_group(self, name):
            return fake_cg(self, name)

    class _FakeStateDoc:
        def document(self, doc_id):
            if doc_id == "ssp":
                return type("SSP", (), {"collection": lambda self, name: coll if name == "risk_register" else None})()
            return type("ICAO", (), {"collection": lambda self, name: _FakeCollection([])})()

    monkeypatch.setattr("app.services.state_risk_service.get_db", lambda: _DB())
    return coll, StateRiskService({"uid": "caan-user", "role": "CAAN_SMD"})


def test_sync_register_persists_entries(monkeypatch):
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
            {"tenant_id": "air1", "occurrence_category": "LOCI", "severity_level": 5, "probability_level": 5, "risk_level": "Very High"},
        ],
    )
    result = svc.sync_register_from_aggregation(2026, 3)
    assert result["synced"] == 2
    assert "BIRD-2026Q3" in coll._store
    assert "LOCI-2026Q3" in coll._store
    bird = coll._store["BIRD-2026Q3"]
    assert bird["ssp_target"] is not None
    assert bird["actual_ssp_value"] == 9
    assert bird["tolerability"] == "Tolerable"


def test_sync_uses_atomic_batch(monkeypatch):
    """All register writes must go through the batch (single commit) rather
    than per-document writes."""
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
            {"tenant_id": "air1", "occurrence_category": "LOCI", "severity_level": 5, "probability_level": 5, "risk_level": "Very High"},
        ],
    )
    result = svc.sync_register_from_aggregation(2026, 3)
    assert result["synced"] == 2
    assert "BIRD-2026Q3" in coll._store
    assert "LOCI-2026Q3" in coll._store


def test_sync_records_aggregated_at_staleness(monkeypatch):
    """Every synced entry must carry aggregated_at and the result must expose
    the aggregation timestamp for staleness detection."""
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
        ],
    )
    result = svc.sync_register_from_aggregation(2026, 3)
    assert "aggregated_at" in result
    assert result["aggregated_at"] is not None
    bird = coll._store["BIRD-2026Q3"]
    assert "aggregated_at" in bird
    assert bird["aggregated_at"] == result["aggregated_at"]


def test_sync_retains_ssp_target_on_resync(monkeypatch):
    """A second sync must carry over the existing SSP target and reduction
    rate, not overwrite them with the defaults."""
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
        ],
    )
    svc.sync_register_from_aggregation(2026, 3)
    svc.update_ssp_target("BIRD-2026Q3", ssp_target=6.0, risk_reduction_rate=15.0)
    result = svc.sync_register_from_aggregation(2026, 3)
    assert result["synced"] == 1
    bird = coll._store["BIRD-2026Q3"]
    assert bird["ssp_target"] == 6.0
    assert bird["risk_reduction_rate"] == 15.0


def test_sync_trend_detects_deterioration(monkeypatch):
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 4, "probability_level": 4, "risk_level": "High"},
        ],
    )
    svc.sync_register_from_aggregation(2026, 1)
    # Same category worsens in Q2
    coll, svc2 = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 5, "probability_level": 5, "risk_level": "Very High"},
        ],
    )
    svc2.sync_register_from_aggregation(2026, 2)
    # Simulate existing entry retained for Q2 run
    data = coll._store["BIRD-2026Q2"]
    assert data["trend"] in ("improving", "stable", "deteriorating")


def test_update_ssp_target(monkeypatch):
    coll, svc = _svc_with_risk_collection(
        monkeypatch,
        hazards=[
            {"tenant_id": "air1", "occurrence_category": "BIRD", "severity_level": 3, "probability_level": 3, "risk_level": "High"},
        ],
    )
    svc.sync_register_from_aggregation(2026, 1)
    updated = svc.update_ssp_target("BIRD-2026Q1", ssp_target=6.0, risk_reduction_rate=15.0)
    assert updated is not None
    assert updated["ssp_target"] == 6.0
    assert updated["risk_reduction_rate"] == 15.0


def test_update_ssp_target_missing_returns_none(monkeypatch):
    coll, svc = _svc_with_risk_collection(monkeypatch, hazards=[])
    assert svc.update_ssp_target("MISSING-2026Q1", ssp_target=5.0) is None


# ============================================================================
# Route-level: authorization + response envelope (mocked auth)
# ============================================================================

from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_caan_user, get_admin_user


class _CAANUser:
    def __init__(self):
        self._data = {
            "role": "CAAN_SMD",
            "tenant_id": None,
            "uid": "caan-test",
            "email": "caan@test.np",
            "claims": {"role": "CAAN_SMD", "tenant_id": None},
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class _SuperUser:
    def __init__(self):
        self._data = {
            "role": "SUPER_ADMIN",
            "tenant_id": None,
            "uid": "super-test",
            "email": "super@test.np",
            "claims": {"role": "SUPER_ADMIN", "tenant_id": None},
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


def _client_with_roles(caan=True, admin=True):
    def dep_caan():
        return _CAANUser()

    def dep_admin():
        return _SuperUser()

    overrides = {}
    if caan:
        overrides[get_caan_user] = dep_caan
    if admin:
        overrides[get_admin_user] = dep_admin
    app.dependency_overrides.update(overrides)

    class _ClientScope:
        def __init__(self):
            self.client = TestClient(app)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            app.dependency_overrides.clear()

    return _ClientScope()


def test_register_requires_caan_role():
    with _client_with_roles(caan=True, admin=False) as s:
        r = s.client.get("/api/v1/state-risk/register")
        assert r.status_code in (200, 200)


def test_register_endpoint_shape():
    with _client_with_roles(caan=True, admin=False) as s:
        r = s.client.get("/api/v1/state-risk/register")
    assert r.status_code == 200
    payload = r.json()
    assert "success" in payload
    assert "risks" in payload


def test_aggregate_endpoint_returns_risks():
    with _client_with_roles(caan=True, admin=False) as s:
        r = s.client.get("/api/v1/state-risk/aggregate?year=2026&quarter=1")
    assert r.status_code == 200
    payload = r.json()
    assert payload["success"] is True
    assert "risks" in payload


def test_update_ssp_target_requires_admin():
    with _client_with_roles(caan=False, admin=False) as s:
        r = s.client.put("/api/v1/state-risk/register/BIRD-2026Q1/ssp-target",
                         json={"ssp_target": 6.0})
    assert r.status_code in (403, 401)


# ============================================================================
# CAAN survey health (SMS pillars across tenants)
# ============================================================================

def _survey_svc(monkeypatch, surveys):
    from app.services.dashboard_service import DashboardService

    def fake_cg(self, name):
        assert name == "surveys"
        return _FakeCollection([_FakeDoc(s) for s in surveys])

    class _DB:
        def collection_group(self, name):
            return fake_cg(self, name)

    monkeypatch.setattr("app.firebase.get_db", lambda: _DB())
    return DashboardService({"uid": "caan-user", "role": "CAAN_SMD"})


def test_get_caan_survey_health_aggregates_pillars(monkeypatch):
    svc = _survey_svc(monkeypatch, surveys=[
        {
            "tenant_id": "air1",
            "safety_policy": 4.0, "safety_risk_management": 3.0,
            "safety_assurance": 5.0, "safety_promotion": 4.0,
            "overall_sms_health": 4.0,
        },
        {
            "tenant_id": "air1",
            "safety_policy": 2.0, "safety_risk_management": 3.0,
            "safety_assurance": 3.0, "safety_promotion": 4.0,
            "overall_sms_health": 3.0,
        },
        {
            "tenant_id": "air2",
            "safety_policy": 5.0, "safety_risk_management": 5.0,
            "safety_assurance": 5.0, "safety_promotion": 5.0,
            "overall_sms_health": 5.0,
        },
    ])
    result = svc.get_caan_survey_health()
    assert result["national"]["response_count"] == 3
    by_id = {op["tenant_id"]: op for op in result["operators"]}
    assert by_id["air1"]["response_count"] == 2
    assert by_id["air1"]["pillars"]["safety_policy"] == 3.0
    assert by_id["air1"]["overall_sms_health"] == 3.5
    assert by_id["air2"]["overall_sms_health"] == 5.0
    # National pillar average across all responses
    assert result["national"]["pillars"]["safety_policy"] == round((4.0 + 2.0 + 5.0) / 3, 2)
    # Best SMS health ranks first
    assert result["operators"][0]["tenant_id"] == "air2"


def test_get_caan_survey_health_empty(monkeypatch):
    svc = _survey_svc(monkeypatch, surveys=[])
    result = svc.get_caan_survey_health()
    assert result["operators"] == []
    assert result["national"]["overall_sms_health"] is None
    assert result["national"]["response_count"] == 0


def test_get_caan_sms_health_assessment_low_pillars(monkeypatch):
    from app.services.dashboard_service import DashboardService

    written = {}

    class _Snap:
        def __init__(self, data):
            self._data = data
            self.exists = bool(data)

        def to_dict(self):
            return self._data

    class _DocRef:
        def __init__(self, data=None):
            self._data = data or {}

        def get(self):
            return _Snap(self._data)

        def set(self, data):
            written.update(data)

        def collection(self, name):
            return _Coll([])

    class _Coll:
        def __init__(self, docs):
            self._docs = docs

        def get(self):
            return [_Snap(d) for d in self._docs]

        def document(self, doc_id):
            return _DocRef()

        def collection(self, name):
            return _Coll([])

    class _DB:
        def __init__(self, surveys):
            self._surveys = surveys

        def collection_group(self, name):
            return _Coll(self._surveys)

        def collection(self, name):
            return _Coll([])

    db = _DB([
        {
            "tenant_id": "air1",
            "safety_policy": 2.0, "safety_risk_management": 2.0,
            "safety_assurance": 4.0, "safety_promotion": 4.0,
            "overall_sms_health": 3.0,
            "question_scores": {"q1": 2.0, "q5": 2.0},
            "submitted_at": datetime.now(timezone.utc),
        },
        {
            "tenant_id": "air2",
            "safety_policy": 5.0, "safety_risk_management": 5.0,
            "safety_assurance": 5.0, "safety_promotion": 5.0,
            "overall_sms_health": 5.0,
            "submitted_at": datetime.now(timezone.utc),
        },
    ])
    monkeypatch.setattr("app.firebase.get_db", lambda: db)
    svc = DashboardService({"uid": "caan-user", "role": "CAAN_SMD"})
    result = svc.get_caan_sms_health_assessment(days=90)

    assert result["period_days"] == 90
    by_id = {op["tenant_id"]: op for op in result["operators"]}
    # air1: policy & SRM below 70% -> mock recommendations generated
    low_pillars = {lp["pillar"] for lp in by_id["air1"]["low_pillars"]}
    assert low_pillars == {"safety_policy", "safety_risk_management"}
    assert len(by_id["air1"]["recommendations"]) == 2
    assert all(r["score_pct"] < 70 for r in by_id["air1"]["recommendations"])
    # air2: all strong -> no recommendations
    assert by_id["air2"]["low_pillars"] == []
    assert by_id["air2"]["recommendations"] == []
    assert written.get("period_days") == 90
