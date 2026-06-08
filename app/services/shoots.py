from sqlalchemy.orm import Session

from app.models import Shoot
from app.schemas import ShootCreate, ShootUpdate


def list_shoots(db: Session, brand_id: int | None = None) -> list[Shoot]:
    q = db.query(Shoot)
    if brand_id:
        q = q.filter(Shoot.brand_id == brand_id)
    return q.order_by(Shoot.shoot_date.asc()).all()


def get_shoot(db: Session, shoot_id: int) -> Shoot | None:
    return db.query(Shoot).filter(Shoot.id == shoot_id).first()


def create_shoot(db: Session, data: ShootCreate) -> Shoot:
    shoot = Shoot(**data.model_dump())
    db.add(shoot)
    db.commit()
    db.refresh(shoot)
    return shoot


def update_shoot(db: Session, shoot_id: int, data: ShootUpdate) -> Shoot | None:
    shoot = get_shoot(db, shoot_id)
    if not shoot:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(shoot, field, value)
    db.commit()
    db.refresh(shoot)
    return shoot
