"""Instagram Messaging API integration."""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
_GRAPH_URL = "https://graph.facebook.com/v21.0"


def parse_webhook(payload: dict) -> list[tuple[str, str, str]]:
    """Extract (igsid, text, raw_json) tuples from a Meta webhook payload."""
    results = []
    for entry in payload.get("entry", []):
        for item in entry.get("messaging", []):
            if "message" not in item:
                continue
            sender = item.get("sender", {})
            igsid = sender.get("id")
            if not igsid:
                continue
            text = item["message"].get("text", "")
            raw = json.dumps(item)
            results.append((igsid, text, raw))
    return results


async def get_sender_handle(igsid: str) -> str | None:
    """Resolve an Instagram-Scoped User ID to a username via Graph API."""
    if not igsid.isdigit():
        logger.warning("Rejected non-numeric IGSID: %s", igsid)
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_GRAPH_URL}/{igsid}",
                params={"fields": "username", "access_token": settings.instagram_access_token},
                timeout=10,
            )
        resp.raise_for_status()
        return resp.json().get("username")
    except Exception as exc:
        logger.warning("Failed to resolve IGSID %s: %s", igsid, exc)
        return None
