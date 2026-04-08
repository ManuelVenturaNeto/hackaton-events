"""Health check route."""

import logging

from fastapi import APIRouter

from app.database import db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/health")
def health_check() -> dict:
    """Check API and database health.

    Returns:
        Dict with status and database reachability.
    """
    db_ok = db.is_reachable()
    status = "healthy" if db_ok else "degraded"
    logger.debug("Health check: %s (db=%s)", status, db_ok)
    return {
        "status": status,
        "database": "connected" if db_ok else "unreachable",
    }
