"""Repository for sync run tracking."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import Database

logger = logging.getLogger(__name__)


class SyncRunRepository:
    """Tracks sync/populate/refresh operations in PostgreSQL."""

    def __init__(self, database: Database) -> None:
        self.db = database

    def start_run(self, run_type: str) -> str:
        """Record the start of a sync run. Returns the run UUID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sync_runs (run_type, status) VALUES (%s, %s) RETURNING id",
            (run_type, "running"),
        )
        run_id = str(cur.fetchone()["id"])
        conn.commit()
        return run_id

    def complete_run(
        self,
        run_id: str,
        status: str = "completed",
        events_discovered: int = 0,
        events_inserted: int = 0,
        events_updated: int = 0,
        errors: Optional[list[str]] = None,
    ) -> None:
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """UPDATE sync_runs SET
                completed_at=%s, status=%s, events_discovered=%s,
                events_inserted=%s, events_updated=%s, errors=%s
            WHERE id=%s""",
            (
                now, status, events_discovered, events_inserted,
                events_updated, json.dumps(errors or []), run_id,
            ),
        )
        conn.commit()

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
