"""Pydantic request/response models. Phase 1 ships the read models the
dashboard needs; create/update payloads are added with their routes.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClientOut(ORMModel):
    id: int
    name: str
    business_name: str | None = None
    instagram: str | None = None
    phone: str | None = None


class LeadOut(ORMModel):
    id: int
    source: str
    status: str
    client_id: int | None = None
    first_contact_at: datetime
    last_activity_at: datetime


class ShootOut(ORMModel):
    id: int
    client_id: int
    shoot_date: date | None = None
    raw_received: bool
    editing_started: bool
    editing_completed: bool
    delivery_completed: bool
    payment_status: str


class EditingTaskOut(ORMModel):
    id: int
    file_name: str
    status: str
    shoot_id: int | None = None
    client_id: int | None = None


class DashboardOut(BaseModel):
    new_leads: int = 0
    unreplied_leads: int = 0
    todays_shoots: int = 0
    videos_waiting: int = 0
    pending_deliveries: int = 0
    pending_payments: int = 0
    upcoming_followups: int = 0
