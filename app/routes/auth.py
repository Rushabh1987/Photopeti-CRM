"""Login / logout routes."""
import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

# In-memory failed-attempt tracker: IP → list of failure timestamps
_failed: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300  # 5-minute sliding window


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    recent = [t for t in _failed[ip] if now - t < _WINDOW_SECONDS]
    _failed[ip] = recent
    if len(recent) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again in 5 minutes.",
        )


def _record_failure(ip: str) -> None:
    _failed[ip].append(time.time())


def _clear_failures(ip: str) -> None:
    _failed.pop(ip, None)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": ""})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    # secrets.compare_digest prevents timing attacks
    valid = (
        secrets.compare_digest(username, settings.app_username)
        and secrets.compare_digest(password, settings.app_password)
    )
    if valid:
        _clear_failures(ip)
        request.session["logged_in"] = True
        return RedirectResponse(url="/", status_code=303)

    _record_failure(ip)
    return templates.TemplateResponse(
        request, "login.html", {"error": "Invalid username or password"}, status_code=401
    )


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
