"""Leads routes — Phase 1 (CRUD) and Phase 2 (reply send)."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/leads", tags=["leads"])

# TODO(Phase 1): GET / , GET /{id} , PATCH /{id}
# TODO(Phase 2): POST /{id}/reply
