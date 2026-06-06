"""Dashboard route — Phase 1/5. Serves the home page and /api/dashboard counts."""
from fastapi import APIRouter

router = APIRouter(tags=["dashboard"])

# TODO(Phase 1): GET /              -> render dashboard.html
# TODO(Phase 1): GET /api/dashboard -> DashboardOut aggregated counts
