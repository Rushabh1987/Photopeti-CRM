from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import LeadCreate, LeadOut, LeadUpdate
from app.services import leads as svc

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=list[LeadOut])
def list_leads(db: Session = Depends(get_db)):
    return svc.list_leads(db)


@router.post("/", response_model=LeadOut, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    return svc.create_lead(db, data)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = svc.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    lead = svc.update_lead(db, lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
