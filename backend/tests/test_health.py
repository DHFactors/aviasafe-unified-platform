def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AviaSAFE SMS API"


def test_liveness_endpoint(client):
    resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert data["status"] == "operational"


def test_cors_allows_canonical_frontend_origins(client):
    """The beta/prod hosting sites and custom domain must always pass the CORS
    preflight regardless of a stale ALLOWED_ORIGINS environment variable."""
    from app.main import CANONICAL_ALLOWED_ORIGINS, _allowed_origins

    merged = _allowed_origins()
    for origin in CANONICAL_ALLOWED_ORIGINS:
        assert origin in merged

    for origin in CANONICAL_ALLOWED_ORIGINS:
        resp = client.options(
            "/api/v1/dashboard/airline/sms-health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert resp.status_code == 200, f"preflight rejected for {origin}"
        assert resp.headers.get("access-control-allow-origin") == origin
        assert resp.headers.get("access-control-allow-credentials") == "true"
