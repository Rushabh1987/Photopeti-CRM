# Instagram Ingest — Design Spec
**Date:** 2026-06-11
**Part:** 5 of 6
**Status:** Approved

---

## Goal

Incoming Instagram DMs auto-create leads with conversation history using keyword filtering. No auto-reply. Owner sees new leads in the dashboard and replies manually from Instagram.

---

## Architecture

Four files touched, no new DB tables:

```
app/routes/webhooks.py          — HTTP only: verify handshake + dispatch
app/services/instagram.py       — Meta API: parse payload, resolve IGSID → handle
app/services/leads.py           — add upsert_from_instagram(): lookup chain + create/append
tests/test_instagram_ingest.py  — 3 unit tests
```

---

## Data Flow

```
POST /webhooks/instagram
    ↓
parse_webhook(payload) → [(igsid, text, raw), ...]
    ↓ for each message
get_sender_handle(igsid) → "@username"   [Graph API call]
    ↓
upsert_from_instagram(db, handle, text, raw)
    ↓
    ┌─ 1. leads.instagram_handle == handle? → append Message to that Lead
    ├─ 2. brands.instagram == handle?       → append Message to brand's latest Lead
    ├─ 3. keyword match in text?            → create Lead(instagram_handle) + Message
    └─ 4. no match                          → silently ignore, return None
```

**Key detail:** Instagram webhooks deliver a numeric IGSID, not the @handle. A second Graph API call resolves it:
`GET https://graph.facebook.com/v21.0/{igsid}?fields=username&access_token={token}`

---

## Components

### `routes/webhooks.py`

**GET `/webhooks/instagram`** — Meta verification handshake (called once on webhook registration):
- Params: `hub.mode`, `hub.verify_token`, `hub.challenge`
- If `mode == "subscribe"` and `verify_token == settings.meta_verify_token` → return `hub.challenge` as plain text (200)
- Else → 403

**POST `/webhooks/instagram`** — incoming DM handler:
1. Return 200 immediately (Meta retries on non-200)
2. Check `payload["object"] == "instagram"`, else ignore
3. Loop: `entry → messaging → each message item`
4. Skip non-message events (reads, reactions, typing)
5. Call `instagram.get_sender_handle(igsid)` → handle
6. Call `leads.upsert_from_instagram(db, handle, text, raw)`
7. Log errors per-message, never raise

Route stays under 40 lines — no business logic.

---

### `services/instagram.py`

**`parse_webhook(payload: dict) → list[tuple[str, str, str]]`**
Extracts `(igsid, text, raw_json)` tuples from raw Meta payload. Skips entries with no `message` key. Returns list (one POST can carry multiple messages).

**`get_sender_handle(igsid: str) → str | None`**
Calls Graph API v21.0 to resolve IGSID → username. Returns `None` on any failure (network, expired token). Route skips + logs on `None` — never crashes webhook.

Both functions are pure (no DB), straightforwardly testable with mocks.

---

### `services/leads.py` — `upsert_from_instagram(db, handle, text, raw)`

Three-step lookup chain:

**Step 1 — Returning lead (not yet converted)**
```
leads WHERE instagram_handle == handle ORDER BY created_at DESC LIMIT 1
→ Found: append Message, update last_activity_at, return lead
```

**Step 2 — Existing brand (converted client)**
```
brands WHERE instagram == handle LIMIT 1
→ Found: get brand's most recent lead, append Message, update last_activity_at, return lead
```

**Step 3 — Unknown sender**
```
Keyword filter: any word in settings.lead_keywords found in text.lower()?
    Match   → create Lead(instagram_handle=handle, source="instagram", status="new")
               create Message(direction="in", channel="instagram", body=text, raw=raw)
               return new lead
    No match → return None (silent ignore)
```

Private helpers: `_find_lead_by_handle`, `_find_brand_by_handle`, `_keyword_match` — each independently testable.

---

## Error Handling

- **Webhook POST always returns 200** — errors logged per-message, never raised
- **`get_sender_handle` returns `None` on failure** — route skips that message, logs warning
- **DB errors in `upsert_from_instagram`** — propagate naturally, caught at route boundary, 200 returned to Meta anyway
- **No retry logic** — Meta handles retries on its end
- No defensive try/except wrapping internal code — only at the route boundary

---

## Tests (`tests/test_instagram_ingest.py`)

Uses existing `db_session` fixture (in-memory SQLite, no Meta API calls needed).

**`test_unknown_sender_with_keyword_creates_lead`**
- Call `upsert_from_instagram(db, "newbrand", "I want to book a shoot", "{}")`
- Assert: Lead created with `instagram_handle="newbrand"`, `status="new"`, one Message attached

**`test_unknown_sender_without_keyword_ignored`**
- Call `upsert_from_instagram(db, "randomperson", "hey nice pics!", "{}")`
- Assert: zero Leads, zero Messages

**`test_known_sender_appends_message`**
- Seed: Lead with `instagram_handle="existingbrand"` in DB
- Call `upsert_from_instagram(db, "existingbrand", "following up", "{}")`
- Assert: no new Lead, one Message on existing Lead, `last_activity_at` updated

---

## Configuration

No new env vars needed. Existing vars used:
- `META_VERIFY_TOKEN` — webhook verification
- `INSTAGRAM_ACCESS_TOKEN` — IGSID → username lookup
- `LEAD_KEYWORDS` — comma-separated keyword list (already in `.env`)

---

## Out of Scope

- Auto-reply (owner replies manually from Instagram)
- WhatsApp webhook (separate future work)
- Multi-message batching optimisation
