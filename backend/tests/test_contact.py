# ============================================================================
# FILE: test_contact.py
# PATH: backend/tests/test_contact.py
# PURPOSE: Tests for the public contact form endpoint. The Sender.net call is
#          mocked so the tests never touch the network.
# ============================================================================

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


def _post_contact(client, **overrides):
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "subject": "Feedback",
        "message": "Great product!",
    }
    payload.update(overrides)
    return client.post("/api/v1/contact", json=payload)


def test_contact_submission_success(monkeypatch):
    captured = {}

    def fake_send(payload):
        captured["payload"] = payload
        return {"success": True}

    monkeypatch.setattr("app.routes.contact._send_to_sender", fake_send)
    monkeypatch.setattr(settings, "SENDER_API_KEY", "test-key")

    with TestClient(app) as client:
        resp = _post_contact(client)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["ok"] is True
    payload = captured["payload"]
    assert payload["email"] == "john@example.com"
    assert payload["firstname"] == "John"
    assert payload["lastname"] == "Doe"
    assert payload["fields"]["Subject"] == "Feedback"
    assert payload["fields"]["Message"] == "Great product!"
    assert payload["trigger_automation"] is False


def test_contact_submission_invalid_email(monkeypatch):
    monkeypatch.setattr(settings, "SENDER_API_KEY", "test-key")
    with TestClient(app) as client:
        resp = _post_contact(client, email="not-an-email")
    assert resp.status_code == 422


def test_contact_submission_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "SENDER_API_KEY", "")

    with TestClient(app) as client:
        resp = _post_contact(client)
    assert resp.status_code == 502
    assert "could not deliver" in resp.json()["detail"].lower()


def test_contact_submission_sender_error(monkeypatch):
    def raise_sender(payload):
        raise RuntimeError("Sender API returned HTTP 400")

    monkeypatch.setattr("app.routes.contact._send_to_sender", raise_sender)
    monkeypatch.setattr(settings, "SENDER_API_KEY", "test-key")

    with TestClient(app) as client:
        resp = _post_contact(client)
    assert resp.status_code == 502
    assert "could not deliver" in resp.json()["detail"].lower()


def test_contact_submission_groups_when_list_configured(monkeypatch):
    captured = {}

    def fake_send(payload):
        captured["payload"] = payload
        return {"success": True}

    monkeypatch.setattr("app.routes.contact._send_to_sender", fake_send)
    monkeypatch.setattr(settings, "SENDER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "SENDER_LIST_ID", "grp123")

    with TestClient(app) as client:
        resp = _post_contact(client)
    assert resp.status_code == 200
    assert captured["payload"]["groups"] == ["grp123"]


def test_split_name():
    from app.routes.contact import _split_name

    assert _split_name("John Doe") == ("John", "Doe")
    assert _split_name("John") == ("John", "")
    assert _split_name("") == ("", "")
