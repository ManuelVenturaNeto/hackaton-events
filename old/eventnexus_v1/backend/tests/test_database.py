"""Tests for database initialization and connectivity."""


class TestDatabase:
    """Tests for the Database class."""

    def test_database_is_reachable(self, tmp_db):
        """Database should be reachable after initialization."""
        assert tmp_db.is_reachable() is True

    def test_tables_created(self, tmp_db):
        """All required tables should exist after initialization."""
        conn = tmp_db.get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        expected = {"events", "event_locations", "event_companies", "event_sources", "sync_runs"}
        assert expected.issubset(tables)

    def test_double_init_is_safe(self, tmp_db):
        """Calling initialize() twice should not raise errors."""
        tmp_db.initialize()
        assert tmp_db.is_reachable() is True
