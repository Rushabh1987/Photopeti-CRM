"""ORM models. Every table carries tenant_id (default 1) so multi-tenancy is a
filter, not a migration, when/if the app evolves into a multi-business SaaS.

Status fields are plain strings with documented allowed values to keep SQLite
migrations trivial; swap to native enums under Postgres later if desired.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

DEFAULT_TENANT = 1

# Allowed values (documented; enforced in the service layer):
LEAD_SOURCES = ("instagram", "whatsapp", "call", "manual")
LEAD_STATUSES = ("new", "replied", "follow_up", "converted", "closed")
MSG_DIRECTIONS = ("in", "out")
MSG_CHANNELS = ("instagram", "whatsapp", "call")
PAYMENT_STATUSES = ("pending", "received")
TASK_STATUSES = ("waiting", "in_progress", "done")
REMINDER_STATUSES = ("pending", "sent", "cancelled")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    name: Mapped[str] = mapped_column(String(200))
    business_name: Mapped[str | None] = mapped_column(String(200), default=None)
    instagram: Mapped[str | None] = mapped_column(String(120), default=None, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), default=None, index=True)
    email: Mapped[str | None] = mapped_column(String(200), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    leads: Mapped[list["Lead"]] = relationship(back_populates="client")
    shoots: Mapped[list["Shoot"]] = relationship(back_populates="client")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), default=None)
    source: Mapped[str] = mapped_column(String(20))                              # LEAD_SOURCES
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)   # LEAD_STATUSES
    first_contact_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client: Mapped["Client | None"] = relationship(back_populates="leads")
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
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    shoot_date: Mapped[date | None] = mapped_column(Date, default=None)
    deliverables: Mapped[str | None] = mapped_column(Text, default=None)
    raw_received: Mapped[bool] = mapped_column(Boolean, default=False)
    editing_started: Mapped[bool] = mapped_column(Boolean, default=False)
    editing_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")  # PAYMENT_STATUSES
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2), default=None)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="shoots")
    editing_tasks: Mapped[list["EditingTask"]] = relationship(back_populates="shoot")


class EditingTask(Base):
    __tablename__ = "editing_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    shoot_id: Mapped[int | None] = mapped_column(ForeignKey("shoots.id"), default=None)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), default=None)
    file_name: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    status: Mapped[str] = mapped_column(String(20), default="waiting", index=True)  # TASK_STATUSES
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    shoot: Mapped["Shoot | None"] = relationship(back_populates="editing_tasks")


class Reminder(Base):
    """Audit + idempotency log. The engine checks the latest row per
    (entity, rule_key) against a cooldown before sending again."""
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(default=DEFAULT_TENANT, index=True)
    entity_type: Mapped[str] = mapped_column(String(20))  # lead | shoot | editing_task
    entity_id: Mapped[int] = mapped_column()
    rule_key: Mapped[str] = mapped_column(String(60), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="telegram")
    due_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # REMINDER_STATUSES
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
