"""Tests for the reminder engine."""
from datetime import datetime, timedelta
from unittest.mock import patch

from app.models import Brand, Lead, Reminder
from app.services.reminders import evaluate


def _brand(db, name="Acme Foods"):
    b = Brand(name=name)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def test_unreplied_2h_fires(db_session):
    brand = _brand(db_session)
    lead = Lead(
        brand_id=brand.id,
        source="manual",
        status="new",
        first_contact_at=datetime.utcnow() - timedelta(hours=3),
    )
    db_session.add(lead)
    db_session.commit()

    with patch("app.services.reminders.send_lead_reminder") as mock_send:
        evaluate(db_session)

    mock_send.assert_called_once()
    r = db_session.query(Reminder).filter_by(entity_id=lead.id).first()
    assert r is not None and r.status == "sent"


def test_within_cooldown_no_duplicate(db_session):
    brand = _brand(db_session)
    lead = Lead(
        brand_id=brand.id,
        source="manual",
        status="new",
        first_contact_at=datetime.utcnow() - timedelta(hours=3),
    )
    db_session.add(lead)
    db_session.commit()

    with patch("app.services.reminders.send_lead_reminder"):
        evaluate(db_session)
        evaluate(db_session)  # second run — still within cooldown

    count = db_session.query(Reminder).filter_by(entity_id=lead.id, status="sent").count()
    assert count == 1


def test_replied_lead_no_reminder(db_session):
    brand = _brand(db_session)
    lead = Lead(
        brand_id=brand.id,
        source="manual",
        status="replied",
        first_contact_at=datetime.utcnow() - timedelta(hours=3),
    )
    db_session.add(lead)
    db_session.commit()

    with patch("app.services.reminders.send_lead_reminder") as mock_send:
        evaluate(db_session)

    mock_send.assert_not_called()
    assert db_session.query(Reminder).count() == 0
