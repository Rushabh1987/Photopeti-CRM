# Photopeti CRM

Code-first CRM for a solo food photographer. FastAPI + SQLAlchemy + PostgreSQL (Supabase),
with an in-process reminder engine (APScheduler). Tracks brands, shoots, editing, and
payments. Captures Instagram leads automatically via keyword filtering. Owner reminders
via Telegram.

## Run locally

```bash
uv run uvicorn app.main:app --reload
```

- App: http://127.0.0.1:8000
- Health: http://127.0.0.1:8000/health
- API docs: disabled by default (set `ENABLE_DOCS=true` in `.env` to enable)

On first start all tables are created automatically in Supabase.

## Run on mobile (same WiFi)

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://<your-pc-ip>:8000` on your phone.

## Test

```bash
uv run pytest -q
```

## Environment variables

Copy `.env.example` to `.env` and fill in values. Required:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `APP_SECRET_KEY` | Random secret for session cookies |
| `APP_USERNAME` | Login username |
| `APP_PASSWORD` | Login password |
| `TELEGRAM_BOT_TOKEN` | From @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Client's Telegram chat ID |
| `META_VERIFY_TOKEN` | Chosen string for Meta webhook verification |
| `META_APP_SECRET` | From Meta App Dashboard → Settings → Basic |
| `INSTAGRAM_ACCESS_TOKEN` | From Meta App → Instagram → Generate Token |

## Layout

```
app/
  main.py          entrypoint, middleware, router wiring
  config.py        env settings (pydantic-settings)
  db.py            engine, session factory, init_db()
  models.py        ORM tables (tenant_id on every row)
  schemas.py       Pydantic request/response models
  routes/
    auth.py        login/logout (session-based)
    ui.py          HTML page routes + form handlers
    brands.py      REST API
    leads.py       REST API
    shoots.py      REST API
    dashboard.py   REST API
    webhooks.py    Instagram DM ingest
  services/
    brands.py      brand CRUD
    leads.py       lead CRUD + Instagram upsert
    shoots.py      shoot CRUD
    reminders.py   reminder rule evaluator
    telegram.py    Telegram Bot API sender
    instagram.py   Meta Graph API client
  scheduler/
    jobs.py        APScheduler — runs reminders every 15 min
templates/         Jinja2 + HTMX
static/            CSS
migrations/        SQL to run once in Supabase dashboard
tests/             pytest (24 tests)
```

## Deployment

Deployed on Railway. On every push to `main`, Railway rebuilds and redeploys automatically.

Set `SESSION_HTTPS_ONLY=true` in production environment variables.

## Features

- Brand, lead, shoot management with full CRUD
- Dashboard with live counts
- Search and status filter on leads and brands
- Inline shoot done / editing done checkboxes
- Payment tracking per brand
- Session-based login with rate-limited brute-force protection
- Instagram DM → lead auto-capture (keyword filtered)
- 2-hour unreplied lead reminder via Telegram
- Security headers, webhook signature verification, input validation
