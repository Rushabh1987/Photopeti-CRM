# Photographer CRM

Code-first CRM + task + reminder system for a food photographer. FastAPI +
SQLAlchemy + SQLite, with an in-process reminder engine (APScheduler) and folder
watcher (watchdog). No no-code platforms; the only external services are the
messaging APIs (Instagram, WhatsApp).

## Status
Phase 1 scaffold: foundation (config, DB, models, schemas, app entrypoint) is
implemented and runnable. Routes, services, scheduler, and watcher are stubbed
with signatures and filled in per phase.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in tokens as you reach Phase 2/4
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
Mount the real video folder by editing the `./watched` volume in
`docker-compose.yml`. The watcher only sees files on the machine it runs on.

## Layout
```
app/
  main.py        entrypoint (lifespan wires scheduler/watcher/routers per phase)
  config.py      env settings
  db.py          engine, session, init_db()
  models.py      all ORM tables (tenant_id on every row)
  schemas.py     Pydantic read models
  routes/        webhooks, leads, clients, shoots, tasks, dashboard
  services/      leads, shoots, tasks, reminders, instagram, whatsapp
  scheduler/     APScheduler jobs (reminder engine)
  watcher/       watchdog folder watcher
  templates/     Jinja + HTMX
tests/           pytest
```

## Build phases
1. **MVP** — models, CRUD, dashboard  *(foundation done; routes/services next)*
2. **Instagram + WhatsApp** — webhook ingest + replies
3. **Media watcher** — new video -> editing task
4. **Reminder engine** — rule evaluator -> WhatsApp (templates)
5. **Dashboard polish** — aggregations, inline edits, mobile
6. **Deploy** — Docker, TLS, Meta App Review
