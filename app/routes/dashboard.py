from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Brand, Lead, Shoot
from app.schemas import DashboardOut

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    today = date.today()
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)

    new_leads = db.query(Lead).filter(Lead.status == "new").count()

    unreplied_leads = (
        db.query(Lead)
        .filter(Lead.status == "new", Lead.first_contact_at <= two_hours_ago)
        .count()
    )

    todays_shoots = (
        db.query(Shoot).filter(Shoot.shoot_date == today).count()
    )

    editing_pending = (
        db.query(Shoot)
        .filter(Shoot.shoot_done == True, Shoot.editing_done == False)
        .count()
    )

    payments_pending = (
        db.query(Brand).filter(Brand.payment_done == False).count()
    )

    return DashboardOut(
        new_leads=new_leads,
        unreplied_leads=unreplied_leads,
        todays_shoots=todays_shoots,
        editing_pending=editing_pending,
        payments_pending=payments_pending,
    )
