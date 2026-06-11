# Instagram Ingest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incoming Instagram DMs auto-create leads with conversation history using keyword filtering.

**Architecture:** Thin webhook route dispatches to `services/instagram.py` (Meta API calls) and `services/leads.py` (DB logic). `upsert_from_instagram` does a 3-step lookup chain: existing lead → existing brand → unknown sender + keyword filter. No auto-reply. No new DB tables.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, httpx, pytest, in-memory SQLite for tests.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `app/services/instagram.py` | Rewrite (was TODO stub) | `parse_webhook` + `get_sender_handle` |
| `app/services/leads.py` | Modify | Add `upsert_from_instagram` + private helpers |
| `app/routes/webhooks.py` | Rewrite (was TODO stub) | GET verify + POST dispatch |
| `app/main.py` | Modify | Wire webhooks router |
| `tests/test_instagram_service.py` | Create | Unit tests for instagram.py |
| `tests/test_instagram_ingest.py` | Create | Unit tests for upsert_from_instagram |
| `tests/test_webhooks.py` | Create | Route-level tests |

---

## Task 1: Instagram service — `parse_webhook` + `get_sender_handle`

**Files:**
- Rewrite: `app/services/instagram.py`
- Create: `tests/test_instagram_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_instagram_service.py`:

```python
"""Unit tests for services/instagram.py"""
import json
from unittest.mock import MagicMock, patch

from app.services.instagram import get_sender_handle, parse_webhook


def test_parse_webhook_extracts_messages():
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "messaging": [{
                "sender": {"id": "9999"},
                "recipient": {"id": "1111"},
                "timestamp": 1234567890,
                "message": {"mid": "mid1", "text": "book a shoot"},
            }]
        }]
    }
    results = parse_webhook(payload)
    assert len(results) == 1
    igsid, text, raw = results[0]
    assert igsid == "9999"
    assert text == "book a shoot"
    assert json.loads(raw)["sender"]["id"] == "9999"


def test_parse_webhook_skips_non_message_events():
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "messaging": [{
                "sender": {"id": "9999"},
                "recipient": {"id": "1111"},
                "timestamp": 1234567890,
                "read": {"watermark": 1234567890},
            }]
        }]
    }
    results = parse_webhook(payload)
    assert results == []


def test_get_sender_handle_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"username": "foodbrand", "id": "9999"}
    with patch("app.services.instagram.httpx.get", return_value=mock_resp):
        result = get_sender_handle("9999")
    assert result == "foodbrand"


def test_get_sender_handle_returns_none_on_error():
    with patch("app.services.instagram.httpx.get", side_effect=Exception("network error")):
        result = get_sender_handle("9999")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```
uv run pytest tests/test_instagram_service.py -v
```

Expected: 4 errors — `ImportError` or `cannot import name 'parse_webhook'`

- [ ] **Step 3: Implement `app/services/instagram.py`**

Replace the entire file:

```python
"""Instagram Messaging API integration."""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
_GRAPH_URL = "https://graph.facebook.com/v21.0"


def parse_webhook(payload: dict) -> list[tuple[str, str, str]]:
    """Extract (igsid, text, raw_json) tuples from a Meta webhook payload."""
    results = []
    for entry in payload.get("entry", []):
        for item in entry.get("messaging", []):
            if "message" not in item:
                continue
            igsid = item["sender"]["id"]
            text = item["message"].get("text", "")
            raw = json.dumps(item)
            results.append((igsid, text, raw))
    return results


def get_sender_handle(igsid: str) -> str | None:
    """Resolve an Instagram-Scoped User ID to a username via Graph API."""
    try:
        resp = httpx.get(
            f"{_GRAPH_URL}/{igsid}",
            params={"fields": "username", "access_token": settings.instagram_access_token},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("username")
    except Exception as exc:
        logger.warning("Failed to resolve IGSID %s: %s", igsid, exc)
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```
uv run pytest tests/test_instagram_service.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```
git add app/services/instagram.py tests/test_instagram_service.py
git commit -m "feat: implement instagram parse_webhook and get_sender_handle"
```

---

## Task 2: Lead upsert — `upsert_from_instagram`

**Files:**
- Modify: `app/services/leads.py`
- Create: `tests/test_instagram_ingest.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_instagram_ingest.py`:

```python
"""Unit tests for leads.upsert_from_instagram."""
from app.models import Brand, Lead, Message
from app.services.leads import upsert_from_instagram


def test_unknown_sender_with_keyword_creates_lead(db_session):
    result = upsert_from_instagram(db_session, "newbrand", "I want to book a shoot", "{}")

    assert result is not None
    assert result.instagram_handle == "newbrand"
    assert result.status == "new"
    assert result.source == "instagram"
    msg = db_session.query(Message).first()
    assert msg is not None
    assert msg.body == "I want to book a shoot"
    assert msg.direction == "in"
    assert msg.channel == "instagram"
    assert msg.lead_id == result.id


def test_unknown_sender_without_keyword_ignored(db_session):
    result = upsert_from_instagram(db_session, "randomperson", "hey nice pics!", "{}")

    assert result is None
    assert db_session.query(Lead).count() == 0
    assert db_session.query(Message).count() == 0


def test_known_lead_sender_appends_message(db_session):
    existing = Lead(instagram_handle="existingbrand", source="instagram", status="new")
    db_session.add(existing)
    db_session.commit()

    result = upsert_from_instagram(db_session, "existingbrand", "following up on rates", "{}")

    assert result is not None
    assert result.id == existing.id
    assert db_session.query(Lead).count() == 1
    msg = db_session.query(Message).first()
    assert msg is not None
    assert msg.body == "following up on rates"
    assert msg.lead_id == existing.id


def test_known_brand_sender_appends_message(db_session):
    brand = Brand(name="Acme Foods", instagram="acmefoods")
    db_session.add(brand)
    db_session.flush()
    lead = Lead(brand_id=brand.id, source="manual", status="converted")
    db_session.add(lead)
    db_session.commit()

    result = upsert_from_instagram(db_session, "acmefoods", "need another shoot", "{}")

    assert result is not None
    assert result.id == lead.id
    assert db_session.query(Lead).count() == 1
    assert db_session.query(Message).count() == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```
uv run pytest tests/test_instagram_ingest.py -v
```

Expected: 4 errors — `cannot import name 'upsert_from_instagram'`

- [ ] **Step 3: Implement `upsert_from_instagram` in `app/services/leads.py`**

Add these imports at the top of `app/services/leads.py` (replace existing imports):

```python
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Brand, Lead, Message
from app.schemas import LeadCreate, LeadUpdate
```

Add these functions at the bottom of `app/services/leads.py`:

```python
def upsert_from_instagram(db: Session, handle: str, text: str, raw: str) -> Lead | None:
    """3-step lookup: existing lead → existing brand → unknown+keyword filter."""
    lead = _find_lead_by_handle(db, handle)
    if lead:
        _append_message(db, lead, text, raw)
        return lead

    brand = _find_brand_by_handle(db, handle)
    if brand:
        latest_lead = (
            db.query(Lead)
            .filter(Lead.brand_id == brand.id)
            .order_by(Lead.created_at.desc())
            .first()
        )
        if latest_lead:
            _append_message(db, latest_lead, text, raw)
            return latest_lead

    if _keyword_match(text):
        new_lead = Lead(instagram_handle=handle, source="instagram", status="new")
        db.add(new_lead)
        db.flush()
        _append_message(db, new_lead, text, raw)
        db.commit()
        db.refresh(new_lead)
        return new_lead

    return None


def _find_lead_by_handle(db: Session, handle: str) -> Lead | None:
    return (
        db.query(Lead)
        .filter(Lead.instagram_handle == handle)
        .order_by(Lead.created_at.desc())
        .first()
    )


def _find_brand_by_handle(db: Session, handle: str) -> Brand | None:
    return db.query(Brand).filter(Brand.instagram == handle).first()


def _append_message(db: Session, lead: Lead, text: str, raw: str) -> None:
    db.add(Message(lead_id=lead.id, direction="in", channel="instagram", body=text, raw=raw))
    lead.last_activity_at = datetime.utcnow()
    db.commit()


def _keyword_match(text: str) -> bool:
    keywords = [k.strip() for k in settings.lead_keywords.split(",")]
    return any(kw in text.lower() for kw in keywords)
```

- [ ] **Step 4: Run tests to verify they pass**

```
uv run pytest tests/test_instagram_ingest.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Run full test suite to check for regressions**

```
uv run pytest -v
```

Expected: all existing tests still PASSED

- [ ] **Step 6: Commit**

```
git add app/services/leads.py tests/test_instagram_ingest.py
git commit -m "feat: add upsert_from_instagram with 3-step lookup chain"
```

---

## Task 3: Webhook route — GET verify + POST handler

**Files:**
- Rewrite: `app/routes/webhooks.py`
- Modify: `app/main.py`
- Create: `tests/test_webhooks.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_webhooks.py`:

```python
"""Route-level tests for /webhooks/instagram."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

# Override get_db so POST requests don't need a real DB connection
app.dependency_overrides[get_db] = lambda: MagicMock()
client = TestClient(app)


def test_instagram_verify_success():
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.meta_verify_token = "testtoken"
        response = client.get("/webhooks/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "testtoken",
            "hub.challenge": "challenge123",
        })
    assert response.status_code == 200
    assert response.text == "challenge123"


def test_instagram_verify_wrong_token():
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.meta_verify_token = "correcttoken"
        response = client.get("/webhooks/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrongtoken",
            "hub.challenge": "challenge123",
        })
    assert response.status_code == 403


def test_instagram_webhook_post_returns_200():
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "messaging": [{
                "sender": {"id": "9999"},
                "recipient": {"id": "1111"},
                "timestamp": 1234567890,
                "message": {"mid": "mid1", "text": "book a shoot"},
            }]
        }]
    }
    with patch("app.routes.webhooks.svc_instagram.get_sender_handle", return_value="newbrand"), \
         patch("app.routes.webhooks.svc_leads.upsert_from_instagram", return_value=None):
        response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200


def test_instagram_webhook_post_ignores_non_instagram_object():
    payload = {"object": "whatsapp", "entry": []}
    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```
uv run pytest tests/test_webhooks.py -v
```

Expected: errors — `404 Not Found` (route not registered yet)

- [ ] **Step 3: Implement `app/routes/webhooks.py`**

Replace the entire file:

```python
"""Inbound webhooks — Instagram DM ingestion."""
import logging

from fastapi import APIRouter, Body, Depends, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.services import instagram as svc_instagram
from app.services import leads as svc_leads

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/instagram")
def instagram_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge)
    return Response(status_code=403)


@router.post("/instagram", status_code=200)
def instagram_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
    if payload.get("object") != "instagram":
        return Response(status_code=200)

    for igsid, text, raw in svc_instagram.parse_webhook(payload):
        try:
            handle = svc_instagram.get_sender_handle(igsid)
            if handle is None:
                logger.warning("Could not resolve IGSID %s — skipping", igsid)
                continue
            svc_leads.upsert_from_instagram(db, handle, text, raw)
        except Exception as exc:
            logger.error("Error processing message from IGSID %s: %s", igsid, exc)

    return Response(status_code=200)
```

- [ ] **Step 4: Wire the webhooks router into `app/main.py`**

In `app/main.py`, change the import line:

```python
# Before:
from app.routes import brands, dashboard, leads, shoots, ui

# After:
from app.routes import brands, dashboard, leads, shoots, ui, webhooks
```

And add the router registration after the other `include_router` calls:

```python
app.include_router(webhooks.router)
```

- [ ] **Step 5: Run webhook route tests**

```
uv run pytest tests/test_webhooks.py -v
```

Expected: 4 PASSED

- [ ] **Step 6: Run full test suite**

```
uv run pytest -v
```

Expected: all tests PASSED

- [ ] **Step 7: Commit**

```
git add app/routes/webhooks.py app/main.py tests/test_webhooks.py
git commit -m "Part 5: Instagram ingest — webhook route, GET verify, POST dispatch"
```

---

## Self-Review

**Spec coverage:**
- [x] Meta GET verification handshake — Task 3 GET handler
- [x] POST parse → sender handle + text + raw — Task 1 `parse_webhook`
- [x] IGSID → handle resolution — Task 1 `get_sender_handle`
- [x] Known sender (lead by handle) → append message — Task 2 Step 3, test 3
- [x] Known sender (brand by instagram) → append message — Task 2 Step 3, test 4
- [x] Unknown sender + keyword match → create lead + message — Task 2 Step 3, test 1
- [x] Unknown sender + no keyword → silently ignore — Task 2 Step 3, test 2
- [x] `LEAD_KEYWORDS` from settings — Task 2 `_keyword_match`
- [x] Always return 200 — Task 3 POST handler
- [x] No auto-reply — confirmed out of scope

**Placeholder scan:** No TBDs, TODOs, or vague steps found.

**Type consistency:**
- `parse_webhook` returns `list[tuple[str, str, str]]` — used as `for igsid, text, raw in ...` in route ✓
- `get_sender_handle(igsid: str) → str | None` — checked for None in route ✓
- `upsert_from_instagram(db, handle, text, raw)` — signature consistent across task 2 and task 3 ✓
- `_append_message(db, lead, text, raw)` — called with same args in all 3 lookup paths ✓
