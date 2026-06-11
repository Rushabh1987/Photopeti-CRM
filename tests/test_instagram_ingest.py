"""Unit tests for leads.upsert_from_instagram."""
from app.models import Brand, Lead, Message
from app.services.leads import upsert_from_instagram


def test_unknown_sender_with_keyword_creates_lead(db_session):
    result = upsert_from_instagram(db_session, "newbrand", "I want to book a shoot", "{}")

    assert result is not None
    assert result.instagram_handle == "newbrand"
    assert result.status == "new"
    assert result.source == "instagram"
    msg = db_session.query(Message).first()
    assert msg is not None
    assert msg.body == "I want to book a shoot"
    assert msg.direction == "in"
    assert msg.channel == "instagram"
    assert msg.lead_id == result.id


def test_unknown_sender_without_keyword_ignored(db_session):
    result = upsert_from_instagram(db_session, "randomperson", "hey nice pics!", "{}")

    assert result is None
    assert db_session.query(Lead).count() == 0
    assert db_session.query(Message).count() == 0


def test_known_lead_sender_appends_message(db_session):
    existing = Lead(instagram_handle="existingbrand", source="instagram", status="new")
    db_session.add(existing)
    db_session.commit()

    result = upsert_from_instagram(db_session, "existingbrand", "following up on rates", "{}")

    assert result is not None
    assert result.id == existing.id
    assert db_session.query(Lead).count() == 1
    msg = db_session.query(Message).first()
    assert msg is not None
    assert msg.body == "following up on rates"
    assert msg.lead_id == existing.id


def test_known_brand_sender_appends_message(db_session):
    brand = Brand(name="Acme Foods", instagram="acmefoods")
    db_session.add(brand)
    db_session.flush()
    lead = Lead(brand_id=brand.id, source="manual", status="converted")
    db_session.add(lead)
    db_session.commit()

    result = upsert_from_instagram(db_session, "acmefoods", "need another shoot", "{}")

    assert result is not None
    assert result.id == lead.id
    assert db_session.query(Lead).count() == 1
    assert db_session.query(Message).count() == 1
