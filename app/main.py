"""Application entrypoint.

Run locally:  uvicorn app.main:app --reload
Health check: GET /health

Routers, the reminder scheduler, and the folder watcher are wired in here as
each phase lands (see the commented blocks below).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Phase 4 -> from app.scheduler.jobs import start_scheduler; start_scheduler()
    # Phase 3 -> from app.watcher.folder import start_watcher; start_watcher()
    yield
    # Phase 4 -> stop_scheduler()
    # Phase 3 -> stop_watcher()


app = FastAPI(title="Photographer CRM", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers (uncommented as each phase is generated):
# from app.routes import dashboard, leads, clients, shoots, tasks, webhooks
# app.include_router(dashboard.router)
# app.include_router(leads.router)
# app.include_router(clients.router)
# app.include_router(shoots.router)
# app.include_router(tasks.router)
# app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
