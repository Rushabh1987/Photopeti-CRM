"""CSV export endpoints — triggers a browser file download for each entity."""
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Brand, Lead, Shoot

router = APIRouter(prefix="/exports", tags=["exports"])


def _csv_response(filename: str, headers: list[str], rows: list) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _dated(name: str) -> str:
    return f"{name}-{date.today().isoformat()}.csv"


@router.get("/brands.csv")
def export_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).order_by(Brand.name).all()
    headers = ["id", "name", "instagram", "phone", "email", "notes", "payment_done", "created_at"]
    rows = [
        [
            b.id, b.name, b.instagram or "", b.phone or "", b.email or "",
            b.notes or "", b.payment_done, b.created_at.isoformat(),
        ]
        for b in brands
    ]
    return _csv_response(_dated("brands"), headers, rows)


@router.get("/leads.csv")
def export_leads(db: Session = Depends(get_db)):
    leads = (
        db.query(Lead)
        .options(joinedload(Lead.brand))
        .order_by(Lead.first_contact_at.desc())
        .all()
    )
    headers = [
        "id", "instagram_handle", "brand_name", "source", "status",
        "first_contact_at", "last_activity_at", "created_at",
    ]
    rows = [
        [
            lead.id,
            lead.instagram_handle or "",
            lead.brand.name if lead.brand else "",
            lead.source,
            lead.status,
            lead.first_contact_at.isoformat(),
            lead.last_activity_at.isoformat(),
            lead.created_at.isoformat(),
        ]
        for lead in leads
    ]
    return _csv_response(_dated("leads"), headers, rows)


@router.get("/shoots.csv")
def export_shoots(db: Session = Depends(get_db)):
    shoots = (
        db.query(Shoot)
        .options(joinedload(Shoot.brand))
        .order_by(Shoot.shoot_date.desc().nulls_last(), Shoot.created_at.desc())
        .all()
    )
    headers = [
        "id", "brand_name", "type", "description", "shoot_date",
        "shoot_done", "editing_done", "created_at",
    ]
    rows = [
        [
            s.id,
            s.brand.name,
            s.type,
            s.description or "",
            s.shoot_date.isoformat() if s.shoot_date else "",
            s.shoot_done,
            s.editing_done,
            s.created_at.isoformat(),
        ]
        for s in shoots
    ]
    return _csv_response(_dated("shoots"), headers, rows)
