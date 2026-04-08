"""PostgreSQL database connection manager for Supabase."""

import logging
from pathlib import Path

import psycopg2
import psycopg2.extras

from app.config import settings

logger = logging.getLogger(__name__)

psycopg2.extras.register_uuid()


class Database:
    """PostgreSQL connection manager."""

    def __init__(self, database_url: str = settings.database_url) -> None:
        self.database_url = database_url
        self._conn = None

    def get_connection(self):
        """Get or create a database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self._conn.autocommit = False
        return self._conn

    def initialize(self) -> None:
        """Run all migration SQL files in order."""
        conn = self.get_connection()
        migrations_dir = Path(__file__).parent.parent / "migrations"
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            logger.info("Running migration: %s", sql_file.name)
            conn.cursor().execute(sql_file.read_text())
        conn.commit()
        logger.info("Database migrations completed.")

    def is_reachable(self) -> bool:
        """Check if the database is reachable."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None


db = Database()
