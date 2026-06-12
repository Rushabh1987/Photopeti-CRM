"""HTML page routes and HTMX partial endpoints."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Brand, Lead, Shoot
from app.schemas import BrandCreate, BrandUpdate, LeadCreate, LeadUpdate, ShootCreate, ShootUpdate
from app.services import brands as svc_brands
from app.services import leads as svc_leads
from app.services import shoots as svc_shoots

templates = Jinja2Templates(directory="templates")
router = APIRouter()


# ── Page routes ──────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def index():
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    stats = {
        "new_leads": db.query(Lead).filter(Lead.status == "new").count(),
        "unreplied_leads": db.query(Lead).filter(
            Lead.status == "new", Lead.first_contact_at <= two_hours_ago
        ).count(),
        "todays_shoots": db.query(Shoot).filter(Shoot.shoot_date == today).count(),
        "editing_pending": db.query(Shoot).filter(
            Shoot.shoot_done == True, Shoot.editing_done == False
        ).count(),
        "payments_pending": db.query(Brand).filter(Brand.payment_done == False).count(),
    }
    return templates.TemplateResponse(
        request, "dashboard.html", {"stats": stats, "active": "dashboard"}
    )


@router.get("/brands", response_class=HTMLResponse)
def brands_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    brands = svc_brands.list_brands(db, q=q)
    ctx = {"brands": brands, "q": q, "active": "brands"}
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "partials/brands_results.html", ctx)
    return templates.TemplateResponse(request, "brands.html", ctx)


@router.get("/brands/{brand_id}", response_class=HTMLResponse)
def brand_detail_page(request: Request, brand_id: int, db: Session = Depends(get_db)):
    brand = svc_brands.get_brand(db, brand_id)
    if not brand:
        return RedirectResponse(url="/brands")
    shoots = svc_shoots.list_shoots(db, brand_id=brand_id)
    return templates.TemplateResponse(
        request, "brand_detail.html",
        {"brand": brand, "shoots": shoots, "active": "brands"},
    )


@router.get("/brands/{brand_id}/edit", response_class=HTMLResponse)
def brand_edit_page(request: Request, brand_id: int, db: Session = Depends(get_db)):
    brand = svc_brands.get_brand(db, brand_id)
    if not brand:
        return RedirectResponse(url="/brands")
    return templates.TemplateResponse(
        request, "brand_edit.html",
        {"brand": brand, "active": "brands"},
    )


@router.get("/leads", response_class=HTMLResponse)
def leads_page(request: Request, q: str = "", status: str = "", db: Session = Depends(get_db)):
    leads = svc_leads.list_leads(db, q=q, status=status)
    brand_objs = svc_brands.list_brands(db)
    brands = {b.id: b.name for b in brand_objs}
    ctx = {
        "leads": leads,
        "brands": brands,
        "brand_list": brand_objs,
        "active": "leads",
        "q": q,
        "status": status,
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "partials/leads_results.html", ctx)
    return templates.TemplateResponse(request, "leads.html", ctx)


@router.get("/leads/{lead_id}", response_class=HTMLResponse)
def lead_detail_page(request: Request, lead_id: int, db: Session = Depends(get_db)):
    lead = svc_leads.get_lead(db, lead_id)
    if not lead:
        return RedirectResponse(url="/leads")
    brand_name = lead.brand.name if lead.brand else (
        "@" + lead.instagram_handle if lead.instagram_handle else None
    )
    return templates.TemplateResponse(
        request, "lead_detail.html",
        {"lead": lead, "brand_name": brand_name, "active": "leads"},
    )


@router.get("/leads/{lead_id}/edit", response_class=HTMLResponse)
def lead_edit_page(request: Request, lead_id: int, db: Session = Depends(get_db)):
    lead = svc_leads.get_lead(db, lead_id)
    if not lead:
        return RedirectResponse(url="/leads")
    brand_objs = svc_brands.list_brands(db)
    return templates.TemplateResponse(
        request, "lead_edit.html",
        {"lead": lead, "brand_list": brand_objs, "active": "leads"},
    )


# ── Form submissions (POST → redirect) ──────────────────────────────────────

@router.post("/ui/brands", response_class=HTMLResponse)
def create_brand_ui(
    name: str = Form(...),
    instagram: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    svc_brands.create_brand(db, BrandCreate(
        name=name,
        instagram=instagram or None,
        phone=phone or None,
        email=email or None,
        notes=notes or None,
    ))
    return RedirectResponse(url="/brands", status_code=303)


@router.post("/ui/shoots", response_class=HTMLResponse)
def create_shoot_ui(
    brand_id: int = Form(...),
    type: str = Form(...),
    description: str = Form(""),
    shoot_date: str = Form(""),
    db: Session = Depends(get_db),
):
    sd = date.fromisoformat(shoot_date) if shoot_date else None
    svc_shoots.create_shoot(db, ShootCreate(
        brand_id=brand_id,
        type=type,
        description=description or None,
        shoot_date=sd,
    ))
    return RedirectResponse(url=f"/brands/{brand_id}", status_code=303)


@router.post("/ui/leads", response_class=HTMLResponse)
def create_lead_ui(
    brand_id: str = Form(""),
    instagram_handle: str = Form(""),
    source: str = Form("manual"),
    db: Session = Depends(get_db),
):
    bid = int(brand_id) if brand_id else None
    handle = instagram_handle.lstrip("@").strip() or None
    svc_leads.create_lead(db, LeadCreate(brand_id=bid, instagram_handle=handle, source=source))
    return RedirectResponse(url="/leads", status_code=303)


# ── Checkbox toggles ─────────────────────────────────────────────────────────

@router.post("/ui/shoots/{shoot_id}/toggle-shoot-done")
def toggle_shoot_done(shoot_id: int, db: Session = Depends(get_db)):
    shoot = svc_shoots.get_shoot(db, shoot_id)
    svc_shoots.update_shoot(db, shoot_id, ShootUpdate(shoot_done=not shoot.shoot_done))
    return RedirectResponse(url=f"/brands/{shoot.brand_id}", status_code=303)


@router.post("/ui/shoots/{shoot_id}/toggle-editing-done")
def toggle_editing_done(shoot_id: int, db: Session = Depends(get_db)):
    shoot = svc_shoots.get_shoot(db, shoot_id)
    svc_shoots.update_shoot(db, shoot_id, ShootUpdate(editing_done=not shoot.editing_done))
    return RedirectResponse(url=f"/brands/{shoot.brand_id}", status_code=303)


@router.post("/ui/brands/{brand_id}/toggle-payment")
def toggle_payment(brand_id: int, db: Session = Depends(get_db)):
    brand = svc_brands.get_brand(db, brand_id)
    svc_brands.update_brand(db, brand_id, BrandUpdate(payment_done=not brand.payment_done))
    return RedirectResponse(url=f"/brands/{brand_id}", status_code=303)


@router.post("/ui/leads/{lead_id}/status", response_class=HTMLResponse)
def update_lead_status(
    request: Request,
    lead_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    updated = svc_leads.update_lead(db, lead_id, LeadUpdate(status=status))
    if updated.brand:
        brand_name = updated.brand.name
    elif updated.instagram_handle:
        brand_name = "@" + updated.instagram_handle
    else:
        brand_name = None
    return templates.TemplateResponse(
        request, "partials/lead_row.html", {"lead": updated, "brand_name": brand_name}
    )


# ── Edit / delete ────────────────────────────────────────────────────────────

@router.post("/ui/brands/{brand_id}/edit", response_class=HTMLResponse)
def edit_brand_ui(
    brand_id: int,
    name: str = Form(...),
    instagram: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    svc_brands.update_brand(db, brand_id, BrandUpdate(
        name=name,
        instagram=instagram or None,
        phone=phone or None,
        email=email or None,
        notes=notes or None,
    ))
    return RedirectResponse(url=f"/brands/{brand_id}", status_code=303)


@router.post("/ui/brands/{brand_id}/delete", response_class=HTMLResponse)
def delete_brand_ui(brand_id: int, db: Session = Depends(get_db)):
    svc_brands.delete_brand(db, brand_id)
    return RedirectResponse(url="/brands", status_code=303)


@router.post("/ui/leads/{lead_id}/edit", response_class=HTMLResponse)
def edit_lead_ui(
    lead_id: int,
    instagram_handle: str = Form(""),
    brand_id: str = Form(""),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    bid = int(brand_id) if brand_id else None
    handle = instagram_handle.lstrip("@").strip() or None
    svc_leads.update_lead(db, lead_id, LeadUpdate(
        instagram_handle=handle,
        brand_id=bid,
        status=status,
    ))
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@router.post("/ui/leads/{lead_id}/delete", response_class=HTMLResponse)
def delete_lead_ui(lead_id: int, db: Session = Depends(get_db)):
    svc_leads.delete_lead(db, lead_id)
    return RedirectResponse(url="/leads", status_code=303)
