"""Unit tests for services/instagram.py"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
async def test_get_sender_handle_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"username": "foodbrand", "id": "9999"}
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    with patch("app.services.instagram.httpx.AsyncClient", return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_client),
        __aexit__=AsyncMock(return_value=False),
    )):
        result = await get_sender_handle("9999")
    assert result == "foodbrand"


@pytest.mark.asyncio
async def test_get_sender_handle_returns_none_on_error():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("network error"))
    with patch("app.services.instagram.httpx.AsyncClient", return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_client),
        __aexit__=AsyncMock(return_value=False),
    )):
        result = await get_sender_handle("9999")
    assert result is None


@pytest.mark.asyncio
async def test_get_sender_handle_returns_none_on_http_error():
    import httpx as httpx_lib
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx_lib.HTTPStatusError(
        "403", request=MagicMock(), response=MagicMock()
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    with patch("app.services.instagram.httpx.AsyncClient", return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_client),
        __aexit__=AsyncMock(return_value=False),
    )):
        result = await get_sender_handle("9999")
    assert result is None
