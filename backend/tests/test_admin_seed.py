"""Super-Admin web seeding panel tests.

Covers the production_seed service (regulator/tenant creation, bulk import,
seed preview + deploy, audit logs) and the /api/v1/admin/* routes
(SUPER_ADMIN authz + setup-key gate).
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.middleware.auth import get_admin_user, get_current_user


# ============================================================================
# Fake Firestore (top-level collections + tenant subcollections)
# ============================================================================

class _SubRef:
    def __init__(self, db, tid, sub, doc):
        self._db = db
        self._tid = tid
        self._sub = sub
        self._doc = doc

    def delete(self):
        items = self._db._subs.get((self._tid, self._sub), [])
        if self._doc in items:
            items.remove(self._doc)


class _SubSnap:
    def __init__(self, db, tid, sub, doc):
        self._db = db
        self._tid = tid
        self._sub = sub
        self._doc = doc
        self.id = doc.get("id") or "sub-doc"
        self.exists = True
        self.reference = _SubRef(db, tid, sub, doc)

    def to_dict(self):
        return self._doc


class _FakeRef:
    def __init__(self, db, name, doc_id):
        self._db = db
        self._name = name
        self.id = doc_id

    def get(self):
        store = self._db._store_for(self._name)
        if self.id in store:
            return _Snap(dict(store[self.id]), self._db, self._name, self.id, exists=True, ref=self)
        return _Snap({}, self._db, self._name, self.id, exists=False, ref=self)

    def set(self, data, merge=False):
        store = self._db._store_for(self._name)
        if merge and self.id in store:
            merged = dict(store[self.id])
            merged.update(data)
            store[self.id] = merged
        else:
            store[self.id] = dict(data)
        return self

    def delete(self):
        self._db._store_for(self._name).pop(self.id, None)

    def collection(self, sub):
        return _FakeSubColl(self._db, self.id, sub)


class _Snap:
    def __init__(self, data, db, name, doc_id, exists=True, ref=None):
        self._data = data or {}
        self._db = db
        self._name = name
        self.id = self._data.get("id") or doc_id
        self.exists = exists
        self.reference = ref or _FakeRef(db, name, doc_id)

    def to_dict(self):
        return self._data


class _QueryResult:
    def __init__(self, items):
        self._items = items

    def get(self):
        return self._items

    def limit(self, n):
        self._items = self._items[:n]
        return self


class _FakeSubColl:
    def __init__(self, db, tid, sub):
        self._db = db
        self._tid = tid
        self._sub = sub

    def add(self, doc):
        self._db._subs.setdefault((self._tid, self._sub), []).append(dict(doc))
        return _FakeRef(self._db, f"sub:{self._tid}/{self._sub}", len(self._db._subs[(self._tid, self._sub)]) - 1)

    def get(self):
        return [_SubSnap(self._db, self._tid, self._sub, d)
                for d in self._db._subs.get((self._tid, self._sub), [])]

    def where(self, field, op, value):
        items = [_SubSnap(self._db, self._tid, self._sub, d)
                 for d in self._db._subs.get((self._tid, self._sub), [])
                 if d.get(field) == value]
        return _QueryResult(items)

    def limit(self, n):
        return _QueryResult([_SubSnap(self._db, self._tid, self._sub, d)
                             for d in self._db._subs.get((self._tid, self._sub), [])][:n])


class _FakeColl:
    def __init__(self, db, name):
        self._db = db
        self._name = name

    def document(self, doc_id):
        return _FakeRef(self._db, self._name, doc_id)

    def add(self, doc):
        ref = _FakeRef(self._db, self._name, f"{self._name}-{len(self._db._store_for(self._name))}")
        ref.set(doc)
        return ref

    def get(self):
        store = self._db._store_for(self._name)
        return [_Snap(dict(d), self._db, self._name, k, ref=_FakeRef(self._db, self._name, k))
                for k, d in store.items()]

    def where(self, field, op, value):
        store = self._db._store_for(self._name)
        return _QueryResult([_Snap(dict(d), self._db, self._name, k, ref=_FakeRef(self._db, self._name, k))
                             for k, d in store.items() if d.get(field) == value])

    def order_by(self, field, direction="ASCENDING"):
        items = []
        for k, d in self._db._store_for(self._name).items():
            snap = _Snap(dict(d), self._db, self._name, k, ref=_FakeRef(self._db, self._name, k))
            items.append(snap)
        items.sort(key=lambda s: (s.to_dict().get(field) or ""), reverse=(direction == "DESCENDING"))
        return _QueryResult(items)


class _FakeDB:
    def __init__(self):
        self._stores = {"regulators": {}, "tenants": {}, "audit_logs": {}}
        self._subs = {}

    def _store_for(self, name):
        if name not in self._stores:
            self._stores[name] = {}
        return self._stores[name]

    def collection(self, name):
        return _FakeColl(self, name)

    def collection_group(self, name):
        items = []
        for (tid, sub), docs in self._subs.items():
            if sub == name:
                for d in docs:
                    items.append(_SubSnap(self, tid, sub, d))
        return _QueryResult(items)


def _patch_db(monkeypatch, db=None):
    db = db or _FakeDB()
    monkeypatch.setattr("app.services.production_seed.get_db", lambda: db)
    return db


def _patch_secret(monkeypatch, value="test-setup-key"):
    from app.core.config import settings
    monkeypatch.setattr(settings, "SETUP_SECRET", value, raising=False)


def _admin_user(role="SUPER_ADMIN"):
    return {"uid": "super-1", "email": "safety.director@caan.gov.np", "role": role, "tenant_id": None}


# ============================================================================
# Service-level
# ============================================================================

def test_create_regulator_success(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import create_regulator
    doc = create_regulator({
        "id": "dgca", "name": "Directorate General of Civil Aviation",
        "country": "IN", "country_name": "India", "operator_tenant_ids": ["ind-air1"],
    }, _admin_user())
    assert doc["id"] == "dgca"
    assert doc["short_name"] == "DGCA"
    stored = db._stores["regulators"]["dgca"]
    assert stored["name"] == "Directorate General of Civil Aviation"
    assert stored["operator_tenant_ids"] == ["ind-air1"]
    logs = db._stores["audit_logs"]
    assert any(l["action"] == "REGULATOR_CREATED" for l in logs.values())


def test_create_regulator_duplicate(monkeypatch):
    db = _patch_db(monkeypatch)
    db._stores["regulators"]["caan"] = {"id": "caan", "name": "CAAN"}
    from app.services.production_seed import create_regulator
    try:
        create_regulator({"id": "caan", "name": "Civil Aviation Authority of Nepal"}, _admin_user())
        assert False, "expected ValueError"
    except ValueError as e:
        assert "already exists" in str(e)


def test_create_regulator_invalid_id(monkeypatch):
    _patch_db(monkeypatch)
    from app.services.production_seed import create_regulator
    try:
        create_regulator({"id": "Bad ID", "name": "X"}, _admin_user())
        assert False, "expected ValueError"
    except ValueError as e:
        assert "must be lowercase" in str(e)


def test_create_tenant_success(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import create_tenant
    doc = create_tenant({
        "tenant_id": "ind-air1", "name": "IndiAir", "icao": "INA",
        "regulator_id": "dgca", "country": "India",
    }, _admin_user())
    stored = db._stores["tenants"]["ind-air1"]
    assert stored["regulator_id"] == "dgca"
    assert stored["name"] == "IndiAir"
    assert any(l["action"] == "TENANT_CREATED" for l in db._stores["audit_logs"].values())


def test_create_tenant_duplicate(monkeypatch):
    db = _patch_db(monkeypatch)
    db._stores["tenants"]["sita-air"] = {"tenant_id": "sita-air", "name": "Sita Air"}
    from app.services.production_seed import create_tenant
    try:
        create_tenant({"tenant_id": "sita-air", "name": "Sita Air"}, _admin_user())
        assert False, "expected ValueError"
    except ValueError as e:
        assert "already exists" in str(e)


def test_bulk_create_tenants_json(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import bulk_create_tenants
    result = bulk_create_tenants([
        {"tenant_id": "a-air", "name": "A Air"},
        {"tenant_id": "b-air", "name": "B Air"},
        {"tenant_id": "a-air", "name": "Dup"},  # duplicate -> error
    ], _admin_user())
    assert result["ok"] == 2
    assert result["total"] == 3
    assert db._stores["tenants"].keys() >= {"a-air", "b-air"}


def test_preview_seed(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import preview_seed
    plan = preview_seed(actor=_admin_user())
    assert plan["regulator"]["id"] == "caan"
    assert plan["regulator"]["exists"] is False
    assert len(plan["operators"]) == 7
    assert all(o["surveys_existing"] == 0 for o in plan["operators"])


def test_deploy_seed(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import deploy_seed
    result = deploy_seed(force=False, actor=_admin_user())
    assert result["operators"] == 7
    assert db._stores["regulators"]["caan"]["id"] == "caan"
    assert db._stores["regulators"]["caan"]["operator_tenant_ids"]
    # Every operator tagged + has seeded data
    for op in db._stores["tenants"].values():
        assert op.get("regulator_id") == "caan"
    assert db._subs.get(("tara-air", "surveys"))
    assert db._subs.get(("tara-air", "hazards"))
    assert db._subs.get(("tara-air", "reports"))
    assert db._subs.get(("tara-air", "responses"))
    assert any(l["action"] == "SEED_DEPLOY" for l in db._stores["audit_logs"].values())


def test_deploy_seed_skips_existing_surveys(monkeypatch):
    db = _patch_db(monkeypatch)
    db._subs[("tara-air", "surveys")] = [{"tenant_id": "tara-air", "seed_version": "x"}]
    from app.services.production_seed import deploy_seed
    result = deploy_seed(force=False, actor=_admin_user())
    # tara-air's existing surveys are not replaced (other operators are seeded)
    assert "tara-air: surveys exist, skipped" in result["details"]
    assert len(db._subs[("tara-air", "surveys")]) == 1
    assert db._subs[("tara-air", "surveys")][0]["seed_version"] == "x"


def test_list_audit_logs(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import _audit, list_audit_logs
    for i in range(3):
        _audit("SEED_PREVIEW", _admin_user(), "caan", f"entry {i}")
    logs = list_audit_logs(limit=10)
    assert len(logs) == 3
    assert logs[0]["action"] == "SEED_PREVIEW"


def test_list_tenants_admin_counts(monkeypatch):
    db = _patch_db(monkeypatch)
    db._stores["tenants"]["tara-air"] = {"tenant_id": "tara-air", "name": "Tara Air"}
    db._subs[("tara-air", "surveys")] = [{"x": 1}, {"x": 2}]
    from app.services.production_seed import list_tenants_admin
    rows = list_tenants_admin()
    assert rows[0]["counts"]["surveys"] == 2


# ============================================================================
# Route-level
# ============================================================================

def _client(user=None):
    app.dependency_overrides[get_admin_user] = lambda: user or _admin_user()
    return TestClient(app)


def test_admin_routes_require_token():
    # No override -> real get_current_user -> 401/403
    resp = TestClient(app).get("/api/v1/admin/seed/preview")
    assert resp.status_code in (401, 403)


def test_admin_routes_403_non_super(monkeypatch):
    _patch_db(monkeypatch)
    # Override the *underlying* get_current_user so get_admin_user's real check
    # runs and rejects a non-SUPER_ADMIN role.
    app.dependency_overrides[get_current_user] = lambda: _admin_user(role="AIRLINE_ADMIN")
    try:
        resp = TestClient(app).get("/api/v1/admin/seed/preview")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert resp.status_code == 403


def test_admin_create_regulator_route(monkeypatch):
    _patch_db(monkeypatch)
    _patch_secret(monkeypatch)
    resp = _client().post("/api/v1/admin/regulators", json={
        "setup_key": "test-setup-key",
        "regulator": {"id": "caan", "name": "Civil Aviation Authority of Nepal",
                      "country": "NP", "country_name": "Nepal"},
    })
    assert resp.status_code == 200
    assert resp.json()["regulator"]["id"] == "caan"


def test_admin_create_regulator_wrong_key(monkeypatch):
    _patch_db(monkeypatch)
    _patch_secret(monkeypatch)
    resp = _client().post("/api/v1/admin/regulators", json={
        "setup_key": "wrong", "regulator": {"id": "caan", "name": "CAAN"},
    })
    assert resp.status_code == 403


def test_admin_seed_preview_route(monkeypatch):
    _patch_db(monkeypatch)
    resp = _client().get("/api/v1/admin/seed/preview")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert len(resp.json()["operators"]) == 7


def test_admin_seed_deploy_route(monkeypatch):
    db = _patch_db(monkeypatch)
    _patch_secret(monkeypatch)
    resp = _client().post("/api/v1/admin/seed/deploy", json={"setup_key": "test-setup-key", "force": False})
    assert resp.status_code == 200
    assert resp.json()["result"]["operators"] == 7
    assert "caan" in db._stores["regulators"]


def test_admin_seed_logs_route(monkeypatch):
    db = _patch_db(monkeypatch)
    from app.services.production_seed import _audit
    _audit("SEED_PREVIEW", _admin_user(), "caan", "hello")
    resp = _client().get("/api/v1/admin/seed/logs?limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["logs"]) == 1


def test_admin_bulk_tenants_csv_route(monkeypatch):
    db = _patch_db(monkeypatch)
    _patch_secret(monkeypatch)
    csv_text = "tenant_id,name,icao,country,regulator_id\nx-air,X Air,XA,Nepal,caan\ny-air,Y Air,YA,Nepal,caan\n"
    resp = _client().post("/api/v1/admin/tenants/bulk", json={"setup_key": "test-setup-key", "csv": csv_text})
    assert resp.status_code == 200
    assert resp.json()["ok"] == 2
    assert "x-air" in db._stores["tenants"]


def test_admin_list_tenants_route(monkeypatch):
    db = _patch_db(monkeypatch)
    db._stores["tenants"]["tara-air"] = {"tenant_id": "tara-air", "name": "Tara Air"}
    resp = _client().get("/api/v1/admin/tenants")
    assert resp.status_code == 200
    assert resp.json()["tenants"][0]["id"] == "tara-air"
