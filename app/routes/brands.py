from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import BrandCreate, BrandOut, BrandUpdate
from app.services import brands as svc

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/", response_model=list[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return svc.list_brands(db)


@router.post("/", response_model=BrandOut, status_code=201)
def create_brand(data: BrandCreate, db: Session = Depends(get_db)):
    return svc.create_brand(db, data)


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = svc.get_brand(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: int, data: BrandUpdate, db: Session = Depends(get_db)):
    brand = svc.update_brand(db, brand_id, data)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand
