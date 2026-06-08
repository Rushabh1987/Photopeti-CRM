PHOTOGRAPHER CRM — PROJECT EXPLANATION
(Context brief for Claude Code. Read this first to understand intent, then follow PLAN.md for build steps.)

## WHAT THIS IS

A small, code-first CRM built for one solo food photographer. It captures Instagram leads
automatically, tracks every shoot from booking to payment under each brand, and nudges the owner
when a lead goes unreplied. It is a real, owned web application — not a collection of no-code
automation tools — and it is designed so it could later grow into a multi-business SaaS without
being rewritten.

## WHO IT IS FOR AND THE PROBLEM IT SOLVES

The user is a food photographer who runs his business mostly through Instagram DMs. His problems, in his own words:

- He sometimes forgets to reply to Instagram leads, so he loses work.
- He has no single place where brands, shoots, editing status, and payments are tracked.
- He does not want to maintain Excel sheets by hand.

So the core value is simple: nothing falls through the cracks. Every lead is logged automatically,
every shoot's stages are tracked per brand, and the system nudges him when a lead goes unreplied.
He should be able to run his whole pipeline from his phone or laptop without manual bookkeeping.

## WHY IT IS BUILT THIS WAY

- Code-first: all logic lives in the application's own code (Python/FastAPI). No n8n, Make, Zapier,
  Bubble, Retool, or Airtable automations. The only outside services are messaging platforms that
  literally cannot be self-hosted — Instagram and WhatsApp. This keeps the system owned,
  maintainable, debuggable, and free to evolve.

- Persistent data only: everything is stored in a hosted PostgreSQL database (Supabase) through
  SQLAlchemy. Nothing is temporary or in-memory. Data must survive app restarts, crashes, and
  redeploys. When in doubt, persist it.

- Cheapest practical setup: open-source libraries, runs on the owner's PC or a ~$5 VPS. No paid
  platforms required to operate it.

- Simple now, scalable later: the smallest architecture that does the job, but every database table
  already carries a tenant_id, so turning this into a multi-photographer SaaS later is an additive
  change (auth + per-tenant filtering), not a rewrite.

## HOW IT WORKS (THE MENTAL MODEL)

Think of it as three jobs that feed one database and one dashboard.

1. CAPTURE — leads arrive automatically from Instagram and become records:
   - Instagram DMs -> via the official Instagram Messaging API webhook (dedicated business account)
   - On each incoming DM, the app checks two things in order:
     1. Is the sender already a known brand? YES -> append message to their existing conversation.
     2. Unknown sender -> scan message for lead keywords (book, shoot, rate, price, available, hire,
        quote, inquiry, package, how much, cost, interested, collaboration, project, photography).
        Match -> auto-create brand + lead + message. No match -> silently ignore.
   - Keywords are configurable via LEAD_KEYWORDS in .env.
   - A lead moves through: new -> replied -> follow_up -> converted -> closed.

2. TRACK — when a lead converts, the owner manually creates Shoots under that Brand. The hierarchy
   is: Brand → many Shoots. Each shoot row has: type (photo/video), description, scheduled date,
   and two checkboxes the owner ticks manually — shoot_done and editing_done. Payment is tracked at
   the brand level with a single payment_done checkbox, because the photographer invoices the brand
   once for all shoots in a batch, not per individual shoot.

3. REMIND — a background job runs every 15 minutes and checks one rule: if a lead status is still
   "new" and more than 2 hours have passed since first contact, send the owner a WhatsApp message
   (via a pre-approved template). The nudge repeats every 2 hours until the owner replies and updates
   the lead status. The reminder log in the database prevents duplicate/spam sends. All other
   tracking (editing, payment) is visible on the dashboard — the owner monitors it himself, no
   automated nudges.

Everything above surfaces on ONE dashboard (server-rendered, works on phone and desktop) showing:
new leads, unreplied leads, today's shoots, editing pending, and payments pending per brand.
The owner ticks checkboxes inline from this UI.

## THE PIECES (AND WHERE LOGIC LIVES)

- FastAPI app, single process. Routes are thin; business logic lives in a services layer.
- SQLAlchemy models: brands, leads, messages, shoots, reminders.
- APScheduler runs the reminder rule-evaluator in-process (one rule: lead_unreplied_2h).
- httpx makes the outbound calls to Instagram/WhatsApp.
- Jinja2 + HTMX render the dashboard. (Could be swapped for React/Next if it becomes a SaaS.)
- The only state of record is the database; the messaging APIs only carry messages, they hold no
  business logic.

## IMPORTANT CONSTRAINTS CLAUDE CODE SHOULD RESPECT

- Instagram is the only lead capture channel. A dedicated Instagram Business account is required —
  not a personal account. Never use scraping or browser automation against Instagram; it violates
  Meta's terms and gets accounts banned.
- Not every DM is a lead. The app uses keyword filtering to decide: known senders get their message
  appended silently; unknown senders are only logged as leads if the message contains a lead keyword.
  This is fully automatic — no manual review step.
- Replies to Instagram leads must be sent within 24 hours of the client's last message (Meta policy).
- Reminders to the owner go via WhatsApp using pre-approved message templates (HSM), which are
  allowed outside the 24h window by the WhatsApp Cloud API.
- Instagram requires a Professional (Business/Creator) account connected to a Facebook Page, plus
  Meta App Review for production.
- Keep secrets in a .env file (never committed). The database lives on Supabase — never commit credentials.

## WHAT SUCCESS LOOKS LIKE

The photographer opens one page on his phone and sees exactly what needs attention today: who to
reply to, which shoots are pending editing, which brands haven't paid. He never manually logs a
lead from Instagram, and he gets a WhatsApp nudge if he forgets to reply to someone. The whole
thing runs on his own PC or a cheap server, and the code is his to extend.

## HOW TO USE THIS WITH THE OTHER FILES

- This file = the "why" and the mental model.
- PLAN.md = the "what to build", broken into numbered Parts to implement one at a time.
- README.md = how to run, test, and deploy.
  Build the Parts in order; commit after each; keep all logic in code.
