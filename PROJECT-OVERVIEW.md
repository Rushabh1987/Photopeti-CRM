PHOTOGRAPHER CRM — PROJECT EXPLANATION
(Context brief for Claude Code. Read this first to understand intent, then follow PLAN.md for build steps.)

## WHAT THIS IS

A small, code-first CRM with task tracking and automatic reminders, built for one solo food
photographer. It captures every incoming lead, tracks every shoot from booking to payment, and
nudges the owner until each pending thing is done. It is a real, owned web application — not a
collection of no-code automation tools — and it is designed so it could later grow into a
multi-business SaaS without being rewritten.

## WHO IT IS FOR AND THE PROBLEM IT SOLVES

The user is a food photographer who runs his business mostly through Instagram DMs, with some
WhatsApp messages and phone calls. His problems, in his own words:

- He sometimes forgets to reply to Instagram leads, so he loses work.
- He shoots for a client, then forgets that the editing is still pending.
- He has no single place where leads and shooting tasks are tracked.
- He wants to be reminded, repeatedly, until a task is actually finished.
- He does not want to maintain Excel sheets by hand.

So the core value is simple: nothing falls through the cracks. Every lead is logged, every shoot's
stages are tracked, and the system keeps reminding him until he acts. He should be able to run his
whole pipeline from his phone or laptop without manual bookkeeping.

## WHY IT IS BUILT THIS WAY

- Code-first: all logic lives in the application's own code (Python/FastAPI). No n8n, Make, Zapier,
  Bubble, Retool, or Airtable automations. The only outside services are messaging platforms that
  literally cannot be self-hosted — Instagram and WhatsApp. This keeps the system owned,
  maintainable, debuggable, and free to evolve.

- Persistent data only: everything is stored in a real on-disk database (SQLite now, PostgreSQL
  later) through SQLAlchemy. Nothing is temporary or in-memory. Data must survive app restarts,
  crashes, and redeploys. When in doubt, persist it.

- Cheapest practical setup: open-source libraries, runs on the owner's PC or a ~$5 VPS. No paid
  platforms required to operate it.

- Simple now, scalable later: the smallest architecture that does the job, but every database table
  already carries a tenant_id, so turning this into a multi-photographer SaaS later is an additive
  change (auth + per-tenant filtering), not a rewrite.

## HOW IT WORKS (THE MENTAL MODEL)

Think of it as three jobs that feed one database and one dashboard.

1. CAPTURE — leads arrive automatically from three channels and become records:
   - Instagram DMs -> via the official Instagram Messaging API webhook
   - WhatsApp messages -> via the official WhatsApp Cloud API webhook
   - Phone calls -> the owner's Android phone POSTs call events to a /webhooks/call endpoint
     Every incoming message is matched to a client (by Instagram handle or phone number) or creates a
     new one, is appended to that lead's conversation history, and sets/updates the lead's status.
     A lead moves through: new -> replied -> follow_up -> converted -> closed.

2. TRACK — when a lead converts, the owner creates a Shoot. A shoot tracks its real-life stages as
   simple flags: raw files received, editing started, editing completed, delivery completed, and
   payment (pending/received). Separately, a folder watcher runs on the PC where the camera/phone
   videos are copied; when a new video file appears, it automatically creates an "editing task" so
   the owner can never forget that footage is waiting to be edited.

3. REMIND — a background job runs every 15 minutes and checks a set of rules. If something is
   overdue, it sends the owner a WhatsApp message (via a pre-approved template), and it keeps reminding on an interval until the
   owner resolves the underlying condition. The rules:
   - New lead not replied within 2 hours.
   - Shoot done, editing not started within 24 hours.
   - Editing started but pending for 3 days.
   - Delivered but payment still pending after 5 days.
   - A video task left "waiting" for over 24 hours.
     Reminders stop on their own once the owner updates the status that fixes the problem — there is
     no manual "dismiss" step. The reminder log in the database prevents duplicate/spam sends.

Everything above surfaces on ONE dashboard (server-rendered, works on phone and desktop) showing:
new leads, unreplied leads, today's shoots, videos waiting for editing, pending deliveries, pending
payments, and upcoming follow-ups. The owner can change any status inline from this UI.

## THE PIECES (AND WHERE LOGIC LIVES)

- FastAPI app, single process. Routes are thin; business logic lives in a services layer.
- SQLAlchemy models: clients, leads, messages, shoots, editing_tasks, reminders.
- APScheduler runs the reminder rule-evaluator in-process.
- watchdog runs the folder watcher in a background thread.
- httpx makes the outbound calls to Instagram/WhatsApp.
- Jinja2 + HTMX render the dashboard. (Could be swapped for React/Next if it becomes a SaaS.)
- The only state of record is the database; the messaging APIs only carry messages, they hold no
  business logic.

## IMPORTANT CONSTRAINTS CLAUDE CODE SHOULD RESPECT

- Instagram and WhatsApp can only message a user within 24 hours of that user's last message. This
  is fine for capturing inbound leads and replying. Reminders to the owner go via WhatsApp using
  pre-approved message templates (HSM), which are allowed outside the 24h window by the WhatsApp Cloud API.
- Instagram requires a Professional (Business/Creator) account connected to a Facebook Page, plus
  Meta App Review for production. Never use scraping or browser automation against Instagram or
  WhatsApp — it violates their terms and gets accounts banned.
- The folder watcher only sees files on the machine it runs on, so it must run where the videos are
  actually copied (the owner's PC).
- Keep secrets in a .env file (never committed). Keep the database file out of version control.

## WHAT SUCCESS LOOKS LIKE

The photographer opens one page on his phone and sees exactly what needs attention today: who to
reply to, what to edit, what to deliver, what to collect payment for. He never manually logs a lead
or maintains a spreadsheet, and he gets a WhatsApp nudge whenever something sits too long — until
he handles it. The whole thing runs on his own PC or a cheap server, and the code is his to extend.

## HOW TO USE THIS WITH THE OTHER FILES

- This file = the "why" and the mental model.
- PLAN.md = the "what to build", broken into numbered Parts to implement one at a time.
- README.md = how to run, test, and deploy.
  Build the Parts in order; commit after each; keep all logic in code.
