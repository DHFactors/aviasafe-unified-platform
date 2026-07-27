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
