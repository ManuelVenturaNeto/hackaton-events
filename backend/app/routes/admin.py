"""Admin routes for operational visibility."""

import logging

from fastapi import APIRouter

from app.database import db
from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin")


@router.get("/sync-runs")
def get_sync_runs() -> list[dict]:
    """Get recent sync run history.

    Returns:
        List of sync run records ordered by most recent first.
    """
    repo = SyncRunRepository(db)
    return repo.get_recent_runs()


@router.get("/stats")
def get_stats() -> dict:
    """Get database statistics.

    Returns:
        Dict with event counts and database info.
    """
    event_repo = EventRepository(db)
    return {
        "total_events": event_repo.get_event_count(),
        "database": "connected" if db.is_reachable() else "unreachable",
    }
