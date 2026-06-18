"""Application entrypoint.

Run locally:  uvicorn app.main:app --reload
Health check: GET /health
API docs:     GET /docs  (only when ENABLE_DOCS=true in .env)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import init_db
from app.routes import auth, brands, dashboard, exports, leads, shoots, ui, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.scheduler.jobs import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Photographer CRM",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

_PUBLIC_PATHS = {"/login", "/health"}
_PUBLIC_PREFIXES = ("/static/", "/webhooks/")

_MAX_BODY = settings.max_body_size_mb * 1024 * 1024


# Middleware runs in reverse-declaration order for requests (last declared = outermost).
# Execution order for an incoming request:
#   SessionMiddleware (outermost, via add_middleware)
#   → add_security_headers
#   → require_login
#   → limit_body_size  (innermost @app.middleware)
#   → route handler

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_BODY:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)


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


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'",
    )
    if settings.session_https_only:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# SessionMiddleware is outermost — parses the cookie before require_login runs.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    https_only=settings.session_https_only,
    same_site="lax",
)

app.include_router(auth.router)
app.include_router(ui.router)
app.include_router(brands.router)
app.include_router(leads.router)
app.include_router(shoots.router)
app.include_router(dashboard.router)
app.include_router(exports.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
