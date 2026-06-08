from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ShootCreate, ShootOut, ShootUpdate
from app.services import shoots as svc

router = APIRouter(prefix="/api/shoots", tags=["shoots"])


@router.get("/", response_model=list[ShootOut])
def list_shoots(brand_id: int | None = None, db: Session = Depends(get_db)):
    return svc.list_shoots(db, brand_id=brand_id)


@router.post("/", response_model=ShootOut, status_code=201)
def create_shoot(data: ShootCreate, db: Session = Depends(get_db)):
    return svc.create_shoot(db, data)


@router.get("/{shoot_id}", response_model=ShootOut)
def get_shoot(shoot_id: int, db: Session = Depends(get_db)):
    shoot = svc.get_shoot(db, shoot_id)
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    return shoot


@router.patch("/{shoot_id}", response_model=ShootOut)
def update_shoot(shoot_id: int, data: ShootUpdate, db: Session = Depends(get_db)):
    shoot = svc.update_shoot(db, shoot_id, data)
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    return shoot
