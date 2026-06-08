from sqlalchemy.orm import Session

from app.models import Brand
from app.schemas import BrandCreate, BrandUpdate


def list_brands(db: Session) -> list[Brand]:
    return db.query(Brand).order_by(Brand.created_at.desc()).all()


def get_brand(db: Session, brand_id: int) -> Brand | None:
    return db.query(Brand).filter(Brand.id == brand_id).first()


def create_brand(db: Session, data: BrandCreate) -> Brand:
    brand = Brand(**data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(db: Session, brand_id: int, data: BrandUpdate) -> Brand | None:
    brand = get_brand(db, brand_id)
    if not brand:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(brand, field, value)
    db.commit()
    db.refresh(brand)
    return brand
