"""Reminder rule evaluator.

evaluate(db) is called every REMINDER_INTERVAL_MINUTES. For each rule,
if the condition holds and the last sent reminder is outside the cooldown
window, a WhatsApp message is sent and a Reminder row is logged.
Reminders stop automatically once the lead status changes — no cancellation needed.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Lead, Reminder
from app.services.whatsapp import send_lead_reminder

logger = logging.getLogger(__name__)

_RULE = "lead_unreplied_2h"
_COOLDOWN_H = 2


def evaluate(db: Session) -> None:
    _lead_unreplied_2h(db)


def _lead_unreplied_2h(db: Session) -> None:
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=_COOLDOWN_H)

    stale_leads = (
        db.query(Lead)
        .filter(Lead.status == "new", Lead.first_contact_at <= cutoff)
        .all()
    )

    for lead in stale_leads:
        last_sent = (
            db.query(Reminder)
            .filter_by(entity_type="lead", entity_id=lead.id, rule_key=_RULE, status="sent")
            .order_by(Reminder.sent_at.desc())
            .first()
        )
        if last_sent and last_sent.sent_at and last_sent.sent_at > cutoff:
            continue

        brand_name = lead.brand.name if lead.brand else f"Lead #{lead.id}"
        hours_waiting = (now - lead.first_contact_at).total_seconds() / 3600

        reminder = Reminder(
            entity_type="lead",
            entity_id=lead.id,
            rule_key=_RULE,
            channel="whatsapp",
            due_at=now,
            status="pending",
        )
        db.add(reminder)
        db.flush()

        try:
            send_lead_reminder(brand_name, hours_waiting)
            reminder.status = "sent"
            reminder.sent_at = datetime.utcnow()
        except Exception as exc:
            logger.error("WhatsApp send failed for lead %d: %s", lead.id, exc)
            reminder.status = "cancelled"

        db.commit()
