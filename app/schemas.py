"""Pydantic request/response models."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Brand ---

class BrandOut(ORMModel):
    id: int
    name: str
    instagram: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    payment_done: bool


class BrandCreate(BaseModel):
    name: str
    instagram: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class BrandUpdate(BaseModel):
    name: str | None = None
    instagram: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    payment_done: bool | None = None


# --- Lead ---

class LeadOut(ORMModel):
    id: int
    brand_id: int | None = None
    source: str
    status: str
    first_contact_at: datetime
    last_activity_at: datetime


class LeadCreate(BaseModel):
    brand_id: int | None = None
    source: str = "manual"
    status: str = "new"


class LeadUpdate(BaseModel):
    brand_id: int | None = None
    status: str | None = None


# --- Shoot ---

class ShootOut(ORMModel):
    id: int
    brand_id: int
    type: str
    description: str | None = None
    shoot_date: date | None = None
    shoot_done: bool
    editing_done: bool


class ShootCreate(BaseModel):
    brand_id: int
    type: str
    description: str | None = None
    shoot_date: date | None = None


class ShootUpdate(BaseModel):
    type: str | None = None
    description: str | None = None
    shoot_date: date | None = None
    shoot_done: bool | None = None
    editing_done: bool | None = None


# --- Dashboard ---

class DashboardOut(BaseModel):
    new_leads: int = 0
    unreplied_leads: int = 0
    todays_shoots: int = 0
    editing_pending: int = 0
    payments_pending: int = 0
