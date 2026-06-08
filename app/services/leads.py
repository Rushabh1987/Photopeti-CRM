from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Lead
from app.schemas import LeadCreate, LeadUpdate


def list_leads(db: Session) -> list[Lead]:
    return db.query(Lead).order_by(Lead.created_at.desc()).all()


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
