"""Inbound webhooks — Instagram DM ingestion."""
import logging

from fastapi import APIRouter, Body, Depends, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.services import instagram as svc_instagram
from app.services import leads as svc_leads

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/instagram")
def instagram_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge)
    return Response(status_code=403)


@router.post("/instagram", status_code=200)
def instagram_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
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
