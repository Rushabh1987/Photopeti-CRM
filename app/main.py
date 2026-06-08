"""Application entrypoint.

Run locally:  uvicorn app.main:app --reload
Health check: GET /health
API docs:     GET /docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routes import brands, dashboard, leads, shoots, ui


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Part 4 -> from app.scheduler.jobs import start_scheduler, stop_scheduler
    yield
    # Part 4 -> stop_scheduler()


app = FastAPI(title="Photographer CRM", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
app.include_router(brands.router)
app.include_router(leads.router)
app.include_router(shoots.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}
