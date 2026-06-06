"""Shoots routes — Phase 1."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/shoots", tags=["shoots"])

# TODO(Phase 1): GET / , POST / , PATCH /{id}  (flip raw/editing/delivery/payment)
