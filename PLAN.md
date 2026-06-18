# PLAN.md — Photographer CRM

A code-first CRM for a solo food photographer, built incrementally with Claude Code. Tracks brands, shoots, editing, and payments. Captures Instagram leads automatically. One Telegram nudge when a lead goes unreplied. Implement one **Part** at a time; commit after each.

---

## Hard rules (do not violate)

- **Code-first only.** No n8n / Make / Zapier / Bubble / Retool / Airtable automations. All orchestration and business logic lives in this app's code. The only external services allowed are messaging APIs that can't be self-hosted (Instagram for lead capture; Telegram for owner reminders).
- **Persistent data only.** Everything is stored in a real on-disk database via SQLAlchemy. Nothing in-memory or temporary. Data survives restarts, crashes, and redeploys.
- **Cheapest practical.** Open-source libraries, self-hosted, runs on a PC or a ~$5 VPS.
- **Multi-tenant ready.** Every table has `tenant_id` (default 1) from day one so a single-owner app can later become a multi-business SaaS without a rewrite.

## Tech stack

- Python 3.12 · FastAPI · SQLAlchemy 2.0
- PostgreSQL via Supabase (hosted, persistent, production-ready from day one)
- pydantic-settings (`.env`) · APScheduler (reminders)
- Jinja2 + HTMX frontend (server-rendered, mobile + web) — swappable to React/Next later
- httpx (external APIs) · pytest · Docker + docker-compose

## External services (unavoidable, set up as needed)

| Service                        | Used for                | Note                                                                                       |
| ------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------ |
| Instagram Messaging API        | Capture + reply to DMs  | Dedicated business account required. Facebook Page + Meta App Review for production. No scraping. |
| Telegram Bot API               | Reminders to the owner  | Free, no approval required. Bot created via @BotFather.                                   |

---

## Data model (already built in Part 1)

- **brands** — name, instagram, phone, email, notes, payment_done (bool, default false), tenant_id
- **leads** — source (instagram/manual), status (new/replied/follow_up/converted/closed), first_contact_at, last_activity_at, brand link
- **messages** — conversation history per lead (direction, channel, body, raw payload)
- **shoots** — brand link, type (photo/video), description, shoot_date, shoot_done (bool), editing_done (bool), tenant_id
- **reminders** — audit + idempotency log (entity, rule_key, due_at, sent_at, status)

## Reminder rules (Part 4)

Re-evaluated every 15 min; repeats until the owner resolves the condition (no manual cancel).

| Rule key              | Fires when                                 | Repeat   |
| --------------------- | ------------------------------------------ | -------- |
| `lead_unreplied_2h`   | lead status = new, >2h since first contact | every 2h |

---

## Build parts

### Part 1 — Foundation ✅ (done)

- **Goal:** runnable skeleton + database.
- **Files:** `config.py`, `db.py`, `models.py`, `schemas.py`, `main.py`, `requirements.txt`, Docker, tests.
- **Done when:** `uvicorn app.main:app` runs, `/health` returns ok, `uv run pytest` passes, DB + all tables auto-create at `./data/crm.db`.
- **Note:** models, schemas, and config were refactored in Step 0 (session 2) to match the final design — Brand replaces Client, Shoot simplified, EditingTask removed, Telegram replaced with WhatsApp.

### Part 2 — Core CRUD + dashboard data ✅ (done)

- **Goal:** manage brands, leads, and shoots manually; compute dashboard counts.
- **Files:** `services/brands.py`, `services/leads.py`, `services/shoots.py`; `routes/brands.py`, `routes/leads.py`, `routes/shoots.py`, `routes/dashboard.py`; wire routers in `main.py`.
- **Implement:** list/create/update for brands, leads, shoots; lead status transitions (new → replied → follow_up → converted → closed); shoot checkboxes (shoot_done, editing_done per row; payment_done per brand); `GET /api/dashboard` (new leads, unreplied leads, today's shoots, editing pending, payments pending).
- **Test:** create a brand → add lead → convert → create shoot → tick checkboxes → dashboard counts update.
- **Done when:** every entity is fully manageable via `/docs` and dashboard counts are correct.

### Part 3 — Dashboard UI ✅ (done)

- **Goal:** mobile + web dashboard, brand pages, shoot rows with inline checkboxes.
- **Files:** `templates/base.html`, `templates/dashboard.html`, `templates/leads.html`, `templates/brands.html`, `templates/shoots.html`, `static/` CSS; HTMX-driven inline checkbox updates.
- **Implement:** dashboard cards from `/api/dashboard`; brand page showing all shoots as rows with shoot_done + editing_done checkboxes inline; payment_done checkbox at brand level; lead list with status transitions; responsive layout (phone + desktop).
- **Test:** ticking a checkbox updates the DB and refreshes counts without full page reload.
- **Done when:** the owner can manage his entire pipeline from the browser on phone or desktop.

### Part 4 — Reminder engine ✅ (done)

- **Goal:** Telegram nudge to owner when a new lead goes unreplied for 2 hours.
- **Files:** `services/reminders.py` (RULES + `evaluate(db)`), `services/telegram.py` (httpx sendMessage to Telegram Bot API), `scheduler/jobs.py` (APScheduler every 15 min); start/stop in `main.py` lifespan.
- **Implement:** `lead_unreplied_2h` rule; idempotent via the `reminders` table + 2h cooldown; send Telegram message; log each send.
- **Pending:** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars to be filled with client.

### Part 5 — Instagram ingest ✅ (done)

- **Goal:** incoming Instagram DMs auto-create leads with conversation history using keyword filtering.
- **Files:** `routes/webhooks.py`, `services/instagram.py`, `services/leads.py` (`upsert_from_instagram`).
- **Done:** Meta webhook verification, payload parsing, keyword filtering, lead upsert logic, HMAC signature verification.
- **Pending:** webhook registration in Meta dashboard (requires live deployment URL), Meta App Review for production use.

### Part 6 — Deploy ✅ (done)

- **Goal:** run in production cheaply.
- **Platform:** Railway (Docker-based, auto-deploys on push to main).
- **Pending:** add all env variables in Railway dashboard, generate public domain, set up Meta webhook with live URL.

### Part 7 (optional) — Multi-tenant SaaS

Only if selling to other photographers. Add users/businesses + auth; turn `tenant_id` into a session-scoped filter; per-tenant integration tokens (encrypted); SQLite → PostgreSQL; optionally a React/Next frontend. Core domain logic is wrapped, not rewritten.

---

## Workflow

- Implement one Part, run `uv run pytest`, then commit: `git commit -m "Part N: <what landed>"`.
- Keep secrets in `.env` (gitignored); never commit tokens or `data/`.
- Build order: 1 → 2 → 3 → 4 → 5 → 6. Part 5 needs a Meta developer account; the app is fully usable after Part 4 with manual data entry only.
