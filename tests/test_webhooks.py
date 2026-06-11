"""Route-level tests for /webhooks/instagram."""
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.pop(get_db, None)


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
    payload = {"object": "instagram", "entry": []}
    with patch("app.routes.webhooks.svc_instagram.parse_webhook",
               return_value=[("9999", "book a shoot", "{}")]), \
         patch("app.routes.webhooks.svc_instagram.get_sender_handle", return_value="newbrand"), \
         patch("app.routes.webhooks.svc_leads.upsert_from_instagram", return_value=None):
        response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200


def test_instagram_webhook_post_ignores_non_instagram_object():
    payload = {"object": "whatsapp", "entry": []}
    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200


def test_instagram_webhook_post_skips_on_none_handle():
    """If get_sender_handle returns None, upsert should not be called and 200 returned."""
    payload = {"object": "instagram", "entry": []}
    with patch("app.routes.webhooks.svc_instagram.parse_webhook",
               return_value=[("9999", "book a shoot", "{}")]), \
         patch("app.routes.webhooks.svc_instagram.get_sender_handle", return_value=None), \
         patch("app.routes.webhooks.svc_leads.upsert_from_instagram") as mock_upsert:
        response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
    mock_upsert.assert_not_called()


def test_instagram_verify_empty_token_rejected():
    """Empty META_VERIFY_TOKEN must never pass verification."""
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.meta_verify_token = ""
        response = client.get("/webhooks/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "",
            "hub.challenge": "challenge123",
        })
    assert response.status_code == 403


def test_instagram_webhook_post_returns_200_on_exception():
    """Even if upsert raises, the route must return 200 (Meta retries on non-200)."""
    payload = {"object": "instagram", "entry": []}
    with patch("app.routes.webhooks.svc_instagram.parse_webhook",
               return_value=[("9999", "book a shoot", "{}")]), \
         patch("app.routes.webhooks.svc_instagram.get_sender_handle", return_value="newbrand"), \
         patch("app.routes.webhooks.svc_leads.upsert_from_instagram",
               side_effect=Exception("db error")):
        response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
