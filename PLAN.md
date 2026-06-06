# PLAN.md — Photographer CRM

A code-first CRM + task + reminder system for a solo food photographer, built incrementally with Claude Code. Implement one **Part** at a time; commit after each.

---

## Hard rules (do not violate)

- **Code-first only.** No n8n / Make / Zapier / Bubble / Retool / Airtable automations. All orchestration and business logic lives in this app's code. The only external services allowed are messaging APIs that can't be self-hosted (Instagram, WhatsApp, Telegram).
- **Persistent data only.** Everything is stored in a real on-disk database via SQLAlchemy. Nothing in-memory or temporary. Data survives restarts, crashes, and redeploys.
- **Cheapest practical.** Open-source libraries, self-hosted, runs on a PC or a ~$5 VPS.
- **Multi-tenant ready.** Every table has `tenant_id` (default 1) from day one so a single-owner app can later become a multi-business SaaS without a rewrite.

## Tech stack

- Python 3.12 · FastAPI · SQLAlchemy 2.0
- SQLite now → PostgreSQL later (connection-string change only)
- pydantic-settings (`.env`) · APScheduler (reminders) · watchdog (folder)
- Jinja2 + HTMX frontend (server-rendered, mobile + web) — swappable to React/Next later
- httpx (external APIs) · pytest · Docker + docker-compose

## External services (unavoidable, set up as needed)

| Service                            | Used for                           | Note                                                                                          |
| ---------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------- |
| Instagram Messaging API            | Capture + reply to DMs             | Needs Professional account + Facebook Page + Meta App Review. No scraping.                    |
| WhatsApp Cloud API                 | Capture + reply to messages        | Inbound/replies in 24h window are free.                                                       |
| Telegram Bot API                   | Reminders to the owner             | Free, instant. Chosen channel for all reminders.                                              |
| Android (custom app or MacroDroid) | Log incoming/outgoing/missed calls | POSTs call data to `/webhooks/call`. Custom Kotlin app is the code-first option (sideloaded). |

---

## Data model (already built in Part 1)

- **clients** — name, business_name, instagram, phone, email, notes
- **leads** — source (instagram/whatsapp/call/manual), status (new/replied/follow_up/converted/closed), first_contact_at, last_activity_at, client link
- **messages** — conversation history per lead (direction, channel, body, raw payload)
- **shoots** — client, shoot_date, deliverables, raw_received, editing_started, editing_completed, delivery_completed, payment_status (pending/received), amount, delivered_at
- **editing_tasks** — file_name, file_path, file_created_at, status (waiting/in_progress/done), optional shoot/client link
- **reminders** — audit + idempotency log (entity, rule_key, due_at, sent_at, status)

## Reminder rules (Part 5)

Re-evaluated every 15 min; repeats until the owner resolves the condition (no manual cancel).

| Rule key                  | Fires when                                          | Repeat    |
| ------------------------- | --------------------------------------------------- | --------- |
| `lead_unreplied_2h`       | lead status = new, >2h since first contact          | every 2h  |
| `editing_not_started_24h` | raw received, editing not started, >24h since shoot | every 24h |
| `editing_pending_3d`      | editing started, not completed, >3d since shoot     | every 24h |
| `payment_pending_5d`      | delivered, payment pending, >5d since delivery      | every 24h |
| `video_waiting_24h`       | editing task still "waiting" >24h                   | every 24h |

---

## Build parts

### Part 1 — Foundation ✅ (done)

- **Goal:** runnable skeleton + database.
- **Files:** `config.py`, `db.py`, `models.py`, `schemas.py`, `main.py`, `requirements.txt`, Docker, tests.
- **Done when:** `uvicorn app.main:app` runs, `/health` returns ok, `pytest` passes, DB + all tables auto-create at `./data/crm.db`.

### Part 2 — Core CRUD + dashboard data

- **Goal:** manage clients, leads, shoots, editing tasks by hand; compute dashboard counts.
- **Files:** `services/leads.py`, `services/shoots.py`, `services/tasks.py`; `routes/clients.py`, `routes/leads.py`, `routes/shoots.py`, `routes/tasks.py`, `routes/dashboard.py`; create/update schemas in `schemas.py`; wire routers in `main.py`.
- **Implement:** list/create/update for each entity; status transitions for leads and shoots; set `delivered_at` when delivery flips true; `GET /api/dashboard` (new leads, unreplied leads, today's shoots, videos waiting, pending deliveries, pending payments, upcoming follow-ups).
- **Test:** create a lead → convert → create shoot → flip flags → counts update.
- **Done when:** every entity is fully manageable via `/docs` and dashboard counts are correct.

### Part 3 — Dashboard UI

- **Goal:** mobile + web dashboard and list/edit pages.
- **Files:** `templates/base.html`, `templates/dashboard.html`, `templates/leads.html`, `templates/shoots.html`, `templates/tasks.html`, `static/` CSS; HTMX-driven inline status edits.
- **Implement:** dashboard cards from `/api/dashboard`; list views with inline status changes (HTMX PATCH); responsive layout.
- **Test:** changing a status in the UI updates the DB and refreshes counts without full reload.
- **Done when:** the owner can run the whole business from the browser on phone or desktop.

### Part 4 — Media watcher

- **Goal:** new video on disk → editing task automatically.
- **Files:** `watcher/folder.py`; start/stop in `main.py` lifespan.
- **Implement:** watchdog observer on `WATCH_FOLDER`; on new video file (by extension) create `EditingTask(status="waiting")` storing file_name, file_path, file_created_at; ignore non-video and partial files.
- **Test:** drop a `.mp4` into the folder → a waiting editing task appears.
- **Done when:** copying videos to the folder reliably creates tasks; runs on the PC where files land.

### Part 5 — Reminder engine

- **Goal:** automatic reminders to the owner via Telegram until tasks are done.
- **Files:** `services/reminders.py` (RULES + `evaluate(db)`), `services/telegram.py` (httpx `sendMessage`), `scheduler/jobs.py` (APScheduler every 15 min); start/stop in `main.py` lifespan.
- **Implement:** the five rules above; idempotent via the `reminders` table + per-rule cooldown; send Telegram message; log each send.
- **Test:** create a lead, backdate first_contact >2h, run evaluate → one Telegram message + one reminder row; run again within cooldown → none.
- **Done when:** overdue items reliably nudge the owner and stop once resolved.

### Part 6 — Instagram + WhatsApp ingest

- **Goal:** incoming DMs/messages auto-create leads with conversation history.
- **Files:** `routes/webhooks.py`, `services/instagram.py`, `services/whatsapp.py`, `services/leads.py` (`upsert_from_channel`).
- **Implement:** Meta GET verification handshake; POST parse → normalize (sender, text, raw); `upsert_from_channel` matches client by instagram/phone (else creates), appends message, reuses or creates an open lead; optional reply send within 24h window.
- **Test:** post a sample Meta payload to the webhook → lead + message created; duplicate sender appends to the same lead.
- **Done when:** real DMs land as leads automatically (dev mode first, then App Review for production).

### Part 7 — Phone call logging

- **Goal:** missed/incoming/outgoing calls auto-create or update leads.
- **Files:** `routes/webhooks.py` (`POST /webhooks/call`); separate Kotlin Android app project (sibling repo) OR MacroDroid config.
- **Implement:** webhook accepts caller number + name + type; reuse `upsert_from_channel` with source/channel = call; log a message ("missed call", etc.).
- **Test:** POST a sample call payload → lead created/updated.
- **Done when:** calls on the owner's phone appear as leads.

### Part 8 — Deploy

- **Goal:** run in production cheaply.
- **Files:** `Dockerfile`, `docker-compose.yml` (already present), add Caddy for HTTPS.
- **Implement:** containerize; persist `data/` volume; public HTTPS for webhooks (Caddy on a VPS, or a tunnel for dev); submit Meta App Review.
- **Test:** rebuild container → data persists; webhooks reachable over HTTPS.
- **Done when:** the system runs unattended and survives restarts/redeploys.

### Part 9 (optional) — Multi-tenant SaaS

Only if selling to other photographers. Add users/businesses + auth; turn `tenant_id` into a session-scoped filter; per-tenant integration tokens (encrypted); SQLite → PostgreSQL; optionally a React/Next frontend. Core domain logic is wrapped, not rewritten.

---

## Workflow

- Implement one Part, run `pytest`, then commit: `git commit -m "Part N: <what landed>"`.
- Keep secrets in `.env` (gitignored); never commit tokens or `data/`.
- Build order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Parts 6/7 need external accounts; the app is fully usable after Part 5 with manual + auto-from-folder data.
