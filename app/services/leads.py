import re
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Brand, Lead, Message
from app.schemas import LeadCreate, LeadUpdate


def list_leads(db: Session, q: str = "", status: str = "") -> list[Lead]:
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if q:
        pattern = f"%{q}%"
        query = (
            query.outerjoin(Brand, Lead.brand_id == Brand.id)
            .filter(or_(
                Brand.name.ilike(pattern),
                Lead.instagram_handle.ilike(pattern),
            ))
        )
    return query.order_by(Lead.created_at.desc()).all()


def get_lead(db: Session, lead_id: int) -> Lead | None:
    return db.query(Lead).filter(Lead.id == lead_id).first()


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def update_lead(db: Session, lead_id: int, data: LeadUpdate) -> Lead | None:
    lead = get_lead(db, lead_id)
    if not lead:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    lead.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead


def upsert_from_instagram(db: Session, handle: str, text: str, raw: str) -> Lead | None:
    """3-step lookup: existing lead → existing brand → unknown+keyword filter."""
    lead = _find_lead_by_handle(db, handle)
    if lead:
        _append_message(db, lead, text, raw)
        db.commit()
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
            db.commit()
            return latest_lead
        return None  # known brand, no lead yet — do not treat as unknown sender

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
    # caller owns the transaction


_KEYWORDS: list[str] = [k.strip() for k in settings.lead_keywords.split(",")]


def _keyword_match(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in _KEYWORDS)
