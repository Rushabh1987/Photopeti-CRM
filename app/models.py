"""ORM models. Every table carries tenant_id (default 1) so multi-tenancy is a
filter, not a migration, when/if the app evolves into a multi-business SaaS.

Status fields are plain strings with documented allowed values to keep SQLite
migrations trivial; swap to native enums under Postgres later if desired.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

DEFAULT_TENANT = 1

# Allowed values (documented; enforced in the service layer):
LEAD_SOURCES = ("instagram", "manual")
LEAD_STATUSES = ("new", "replied", "converted", "closed")
MSG_DIRECTIONS = ("in", "out")
MSG_CHANNELS = ("instagram",)
SHOOT_TYPES = ("photo", "video")
REMINDER_STATUSES = ("pending", "sent", "cancelled")


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    name: Mapped[str] = mapped_column(String(200))
    instagram: Mapped[str | None] = mapped_column(String(120), default=None, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), default=None, index=True)
    email: Mapped[str | None] = mapped_column(String(200), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    payment_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    leads: Mapped[list["Lead"]] = relationship(back_populates="brand")
    shoots: Mapped[list["Shoot"]] = relationship(back_populates="brand")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id"), default=None)
    source: Mapped[str] = mapped_column(String(20))                             # LEAD_SOURCES
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)  # LEAD_STATUSES
    first_contact_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand | None"] = relationship(back_populates="leads")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    direction: Mapped[str] = mapped_column(String(4))   # MSG_DIRECTIONS
    channel: Mapped[str] = mapped_column(String(20))    # MSG_CHANNELS
    body: Mapped[str | None] = mapped_column(Text, default=None)
    raw: Mapped[str | None] = mapped_column(Text, default=None)  # JSON payload as received
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead"] = relationship(back_populates="messages")


class Shoot(Base):
    __tablename__ = "shoots"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    type: Mapped[str] = mapped_column(String(10))               # SHOOT_TYPES
    description: Mapped[str | None] = mapped_column(Text, default=None)
    shoot_date: Mapped[date | None] = mapped_column(Date, default=None)
    shoot_done: Mapped[bool] = mapped_column(Boolean, default=False)
    editing_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="shoots")


class Reminder(Base):
    """Audit + idempotency log. The engine checks the latest row per
    (entity_type, entity_id, rule_key) against a cooldown before sending again."""
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    entity_type: Mapped[str] = mapped_column(String(20))  # lead
    entity_id: Mapped[int] = mapped_column()
    rule_key: Mapped[str] = mapped_column(String(60), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    due_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # REMINDER_STATUSES
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
