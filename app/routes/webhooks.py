"""Inbound webhooks — Instagram DM ingestion."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.services import instagram as svc_instagram
from app.services import leads as svc_leads

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(request: Request, body: bytes) -> None:
    """Reject requests whose X-Hub-Signature-256 doesn't match the payload.

    Skipped when META_APP_SECRET is not configured (dev / test mode).
    """
    if not settings.meta_app_secret:
        return
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        settings.meta_app_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


@router.get("/instagram")
def instagram_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    if (hub_mode == "subscribe"
            and settings.meta_verify_token
            and hub_verify_token == settings.meta_verify_token):
        return PlainTextResponse(hub_challenge)
    return Response(status_code=403)


@router.post("/instagram", status_code=200)
async def instagram_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    _verify_signature(request, body)

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return Response(status_code=200)

    if payload.get("object") != "instagram":
        return Response(status_code=200)

    for igsid, text, raw in svc_instagram.parse_webhook(payload):
        try:
            handle = svc_instagram.get_sender_handle(igsid)
            if handle is None:
                logger.warning("Could not resolve IGSID %s — skipping", igsid)
                continue
            svc_leads.upsert_from_instagram(db, handle, text, raw)
        except Exception as exc:
            logger.error("Error processing message from IGSID %s: %s", igsid, exc)

    return Response(status_code=200)
