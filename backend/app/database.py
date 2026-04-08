"""SQLite database setup and connection management."""

import logging
import sqlite3
import threading
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Thread-safe SQLite database manager with connection pooling per thread."""

    _local = threading.local()

    def __init__(self, db_path: str = settings.database_url) -> None:
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_lock = threading.Lock()

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection.

        Returns:
            A sqlite3 Connection for the current thread.
        """
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return conn

    def initialize(self) -> None:
        """Create all required tables if they don't exist."""
        with self._init_lock:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    organizer TEXT NOT NULL,
                    category TEXT NOT NULL,
                    format TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'upcoming',
                    expected_audience_size INTEGER DEFAULT 0,
                    official_website_url TEXT DEFAULT '',
                    brief_description TEXT DEFAULT '',
                    networking_relevance_score REAL DEFAULT 0.0,
                    start_date TEXT DEFAULT '',
                    end_date TEXT DEFAULT '',
                    duration_days INTEGER DEFAULT 0,
                    last_updated TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    dedup_key TEXT UNIQUE
                );

                CREATE TABLE IF NOT EXISTS event_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    venue_name TEXT DEFAULT '',
                    full_street_address TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    state_province TEXT DEFAULT '',
                    country TEXT DEFAULT '',
                    postal_code TEXT DEFAULT '',
                    continent TEXT DEFAULT '',
                    neighborhood TEXT DEFAULT '',
                    street TEXT DEFAULT '',
                    street_number TEXT DEFAULT '',
                    latitude REAL,
                    longitude REAL,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS event_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS event_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_url TEXT DEFAULT '',
                    confidence REAL DEFAULT 1.0,
                    fetched_at TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    events_discovered INTEGER DEFAULT 0,
                    events_inserted INTEGER DEFAULT 0,
                    events_updated INTEGER DEFAULT 0,
                    errors TEXT DEFAULT '[]'
                );

                CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
                CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
                CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
                CREATE INDEX IF NOT EXISTS idx_events_country ON event_locations(country);
                CREATE INDEX IF NOT EXISTS idx_events_city ON event_locations(city);
                CREATE INDEX IF NOT EXISTS idx_events_dedup ON events(dedup_key);
                CREATE INDEX IF NOT EXISTS idx_event_companies_event ON event_companies(event_id);
            """)

            conn.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    def is_reachable(self) -> bool:
        """Check if the database is reachable.

        Returns:
            True if the database can be queried.
        """
        try:
            conn = self.get_connection()
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the thread-local connection if it exists."""
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            conn.close()
            self._local.connection = None


db = Database()
