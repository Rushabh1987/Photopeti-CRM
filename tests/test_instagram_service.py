"""Unit tests for services/instagram.py"""
import json
from unittest.mock import MagicMock, patch

from app.services.instagram import get_sender_handle, parse_webhook


def test_parse_webhook_extracts_messages():
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
    results = parse_webhook(payload)
    assert len(results) == 1
    igsid, text, raw = results[0]
    assert igsid == "9999"
    assert text == "book a shoot"
    assert json.loads(raw)["sender"]["id"] == "9999"


def test_parse_webhook_skips_non_message_events():
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "messaging": [{
                "sender": {"id": "9999"},
                "recipient": {"id": "1111"},
                "timestamp": 1234567890,
                "read": {"watermark": 1234567890},
            }]
        }]
    }
    results = parse_webhook(payload)
    assert results == []


def test_get_sender_handle_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"username": "foodbrand", "id": "9999"}
    with patch("app.services.instagram.httpx.get", return_value=mock_resp):
        result = get_sender_handle("9999")
    assert result == "foodbrand"


def test_get_sender_handle_returns_none_on_error():
    with patch("app.services.instagram.httpx.get", side_effect=Exception("network error")):
        result = get_sender_handle("9999")
    assert result is None
