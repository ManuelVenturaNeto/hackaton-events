"""Repository for sync run tracking."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import Database

logger = logging.getLogger(__name__)


class SyncRunRepository:
    """Tracks sync/populate/refresh operations in SQLite."""

    def __init__(self, database: Database) -> None:
        """Initialize with database reference.

        Args:
            database: The Database instance.
        """
        self.db = database

    def start_run(self, run_type: str) -> int:
        """Record the start of a sync run.

        Args:
            run_type: Type of run ('populate', 'refresh', 'sync').

        Returns:
            The run ID.
        """
        conn = self.db.get_connection()
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO sync_runs (run_type, started_at, status) VALUES (?,?,?)",
            (run_type, now, "running"),
        )
        conn.commit()
        logger.info("Started sync run %d of type %s", cursor.lastrowid, run_type)
        return cursor.lastrowid

    def complete_run(
        self,
        run_id: int,
        status: str = "completed",
        events_discovered: int = 0,
        events_inserted: int = 0,
        events_updated: int = 0,
        errors: Optional[list[str]] = None,
    ) -> None:
        """Mark a sync run as completed.

        Args:
            run_id: The run ID.
            status: Final status ('completed', 'failed').
            events_discovered: Count of events discovered.
            events_inserted: Count of events inserted.
            events_updated: Count of events updated.
            errors: List of error messages.
        """
        conn = self.db.get_connection()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE sync_runs SET
                completed_at=?, status=?, events_discovered=?,
                events_inserted=?, events_updated=?, errors=?
            WHERE id=?""",
            (
                now, status, events_discovered, events_inserted,
                events_updated, json.dumps(errors or []), run_id,
            ),
        )
        conn.commit()
        logger.info("Completed sync run %d with status %s", run_id, status)

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        """Get recent sync runs.

        Args:
            limit: Max number of runs to return.

        Returns:
            List of run records as dicts.
        """
        conn = self.db.get_connection()
        rows = conn.execute(
            "SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
