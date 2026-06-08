# Photographer CRM

Code-first CRM for a food photographer. FastAPI + SQLAlchemy + PostgreSQL (Supabase),
with an in-process reminder engine (APScheduler). Tracks brands, shoots, editing,
and payments. Captures Instagram leads automatically via keyword filtering. No no-code
platforms; only external services are Supabase (database), Instagram (lead capture),
and WhatsApp (owner reminders).

## Status
Phase 1 scaffold: foundation (config, DB, models, schemas, app entrypoint) is
implemented and runnable. Routes, services, scheduler, and watcher are stubbed
with signatures and filled in per phase.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in DATABASE_URL from Supabase dashboard
uvicorn app.main:app --reload
```
- App: http://127.0.0.1:8000
- Health: http://127.0.0.1:8000/health
- API docs (auto): http://127.0.0.1:8000/docs

On first start the SQLite DB is created at `./data/crm.db` and all tables are
generated automatically.

## Test
```bash
pytest -q
```

## Run with Docker
```bash
cp .env.example .env
docker compose up --build
```

## Layout
```
app/
  main.py        entrypoint (lifespan wires scheduler/watcher/routers per phase)
  config.py      env settings
  db.py          engine, session, init_db()
  models.py      all ORM tables (tenant_id on every row)
  schemas.py     Pydantic read models
  routes/        webhooks, leads, brands, shoots, dashboard
  services/      leads, shoots, reminders, instagram, whatsapp
  scheduler/     APScheduler jobs (reminder engine)
  templates/     Jinja + HTMX
tests/           pytest
```

## Build phases
1. **Foundation** — models, DB, health check *(done)*
2. **Core CRUD + dashboard API** — brands, leads, shoots, dashboard counts
3. **Dashboard UI** — Jinja2 + HTMX, brand pages, shoot checkboxes, mobile + web
4. **Reminder engine** — lead_unreplied_2h rule -> WhatsApp template (APScheduler)
5. **Instagram ingest** — keyword-filtered DM capture + replies
6. **Deploy** — Docker, TLS, Meta App Review
