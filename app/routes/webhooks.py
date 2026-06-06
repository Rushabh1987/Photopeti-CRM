"""Inbound webhooks — Phase 2.

GET handlers do the Meta verification handshake; POST handlers parse the
payload and hand off to services.leads.upsert_from_channel().
"""
from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# TODO(Phase 2): GET/POST /instagram
# TODO(Phase 2): GET/POST /whatsapp
# TODO(Phase 2): POST /call   (MacroDroid or custom Android app)
