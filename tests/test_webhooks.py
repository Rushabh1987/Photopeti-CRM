"""Route-level tests for /webhooks/instagram."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

# Override get_db so POST requests don't need a real DB connection
app.dependency_overrides[get_db] = lambda: MagicMock()
client = TestClient(app)


def test_instagram_verify_success():
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.meta_verify_token = "testtoken"
        response = client.get("/webhooks/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "testtoken",
            "hub.challenge": "challenge123",
        })
    assert response.status_code == 200
    assert response.text == "challenge123"


def test_instagram_verify_wrong_token():
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.meta_verify_token = "correcttoken"
        response = client.get("/webhooks/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrongtoken",
            "hub.challenge": "challenge123",
        })
    assert response.status_code == 403


def test_instagram_webhook_post_returns_200():
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "messaging": [{
                "sender": {"id": "9999"},
                "recipient": {"id": "1111"},
                "timestamp": 1234567890,
                "message": {"mid": "mid1", "text": "book a shoot"},
            }]
        }]
    }
    with patch("app.routes.webhooks.svc_instagram.get_sender_handle", return_value="newbrand"), \
         patch("app.routes.webhooks.svc_leads.upsert_from_instagram", return_value=None):
        response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200


def test_instagram_webhook_post_ignores_non_instagram_object():
    payload = {"object": "whatsapp", "entry": []}
    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
