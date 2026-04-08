"""Health check route."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import db

router = APIRouter()


@router.get("/api/health")
def health_check() -> dict:
    db_ok = db.is_reachable()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
