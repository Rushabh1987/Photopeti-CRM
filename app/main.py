"""Application entrypoint.

Run locally:  uvicorn app.main:app --reload
Health check: GET /health
API docs:     GET /docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import init_db
from app.routes import auth, brands, dashboard, leads, shoots, ui, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.scheduler.jobs import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Photographer CRM", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

_PUBLIC_PATHS = {"/login", "/health"}
_PUBLIC_PREFIXES = ("/static/", "/webhooks/")


@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)
    if not request.session.get("logged_in"):
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)
        return RedirectResponse(url="/login", status_code=302)
    return await call_next(request)


# SessionMiddleware must be added after the auth middleware so it becomes the
# outermost layer — it parses the cookie before the auth check runs.
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)

app.include_router(auth.router)
app.include_router(ui.router)
app.include_router(brands.router)
app.include_router(leads.router)
app.include_router(shoots.router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
