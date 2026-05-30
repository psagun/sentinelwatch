"""SentinelWatch API entry point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import settings
from src.database import init_db, close_db


logging.basicConfig(
    level=settings.log_level.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    await init_db()

    # Clean up old monitoring-infrastructure alerts and findings
    from src import database as db
    from src.api.routes import _findings_db, _alerts_db

    INFRA_TITLES = {"website unreachable", "scraping browser could not render"}
    cleaned_findings = 0
    cleaned_alerts = 0

    # Remove infrastructure findings
    kept_findings = []
    for f in _findings_db:
        title = (f.get("title") or "").lower()
        if any(kw in title for kw in INFRA_TITLES):
            await db.delete_finding(f.get("id", ""))
            cleaned_findings += 1
        else:
            kept_findings.append(f)
    _findings_db[:] = kept_findings

    # Remove alerts linked to infrastructure findings
    infa_finding_ids = {f.get("id", "") for f in _findings_db}
    kept_alerts = []
    for a in _alerts_db:
        if a.get("finding_id") in infa_finding_ids:
            cleaned_alerts += 1
        else:
            kept_alerts.append(a)
    _alerts_db[:] = kept_alerts

    if cleaned_findings or cleaned_alerts:
        logger.info(f"Cleaned {cleaned_findings} infra findings and {cleaned_alerts} orphaned alerts")

    yield
    await close_db()
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-Powered Security & Compliance Monitoring Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
    )



