"""Repository for event CRUD operations on SQLite."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import Database
from app.models.event import (
    CompanyModel,
    EventCreate,
    EventResponse,
    LocationModel,
)

logger = logging.getLogger(__name__)


class EventRepository:
    """Handles all event persistence operations against SQLite."""

    def __init__(self, database: Database) -> None:
        """Initialize repository with database reference.

        Args:
            database: The Database instance to use.
        """
        self.db = database

    def _generate_dedup_key(self, event: EventCreate) -> str:
        """Generate a deterministic deduplication key for an event.

        Uses normalized name + organizer + start_date + city + country + url.

        Args:
            event: The event to generate a key for.

        Returns:
            A string dedup key.
        """
        parts = [
            event.name.strip().lower(),
            event.organizer.strip().lower(),
            event.start_date.strip(),
            event.location.city.strip().lower(),
            event.location.country.strip().lower(),
        ]
        if event.official_website_url:
            parts.append(event.official_website_url.strip().lower().rstrip("/"))
        return "|".join(parts)

    def upsert_event(self, event: EventCreate) -> tuple[str, bool]:
        """Insert or update an event using deduplication.

        Args:
            event: The event data to upsert.

        Returns:
            Tuple of (event_id, was_inserted). was_inserted is True for new events.
        """
        conn = self.db.get_connection()
        now = datetime.now(timezone.utc).isoformat()
        dedup_key = self._generate_dedup_key(event)

        existing = conn.execute(
            "SELECT id FROM events WHERE dedup_key = ?", (dedup_key,)
        ).fetchone()

        if existing:
            event_id = existing["id"]
            conn.execute(
                """UPDATE events SET
                    name=?, organizer=?, category=?, format=?, status=?,
                    expected_audience_size=?, official_website_url=?,
                    brief_description=?, networking_relevance_score=?,
                    start_date=?, end_date=?, duration_days=?, last_updated=?
                WHERE id=?""",
                (
                    event.name, event.organizer, event.category.value,
                    event.format.value, event.status.value,
                    event.expected_audience_size, event.official_website_url,
                    event.brief_description, event.networking_relevance_score,
                    event.start_date, event.end_date, event.duration_days,
                    now, event_id,
                ),
            )
            self._upsert_location(conn, event_id, event.location)
            self._replace_companies(conn, event_id, event.companies)
            self._add_source(conn, event_id, event.source_name, event.source_url, event.source_confidence, now)
            conn.commit()
            logger.info("Updated existing event: %s (id=%s)", event.name, event_id)
            return event_id, False

        event_id = uuid.uuid4().hex[:16]
        conn.execute(
            """INSERT INTO events
                (id, name, organizer, category, format, status,
                 expected_audience_size, official_website_url,
                 brief_description, networking_relevance_score,
                 start_date, end_date, duration_days,
                 last_updated, created_at, dedup_key)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id, event.name, event.organizer, event.category.value,
                event.format.value, event.status.value,
                event.expected_audience_size, event.official_website_url,
                event.brief_description, event.networking_relevance_score,
                event.start_date, event.end_date, event.duration_days,
                now, now, dedup_key,
            ),
        )
        self._upsert_location(conn, event_id, event.location)
        self._replace_companies(conn, event_id, event.companies)
        self._add_source(conn, event_id, event.source_name, event.source_url, event.source_confidence, now)
        conn.commit()
        logger.info("Inserted new event: %s (id=%s)", event.name, event_id)
        return event_id, True

    def _upsert_location(self, conn, event_id: str, loc: LocationModel) -> None:
        """Insert or replace location for an event.

        Args:
            conn: Database connection.
            event_id: The event ID.
            loc: Location data.
        """
        conn.execute("DELETE FROM event_locations WHERE event_id=?", (event_id,))
        conn.execute(
            """INSERT INTO event_locations
                (event_id, venue_name, full_street_address, city, state_province,
                 country, postal_code, continent, neighborhood, street,
                 street_number, latitude, longitude)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id, loc.venue_name, loc.full_street_address, loc.city,
                loc.state_province, loc.country, loc.postal_code, loc.continent,
                loc.neighborhood, loc.street, loc.street_number,
                loc.latitude, loc.longitude,
            ),
        )

    def _replace_companies(self, conn, event_id: str, companies: list[CompanyModel]) -> None:
        """Replace all companies for an event.

        Args:
            conn: Database connection.
            event_id: The event ID.
            companies: List of companies.
        """
        conn.execute("DELETE FROM event_companies WHERE event_id=?", (event_id,))
        for company in companies:
            conn.execute(
                "INSERT INTO event_companies (event_id, name, role) VALUES (?,?,?)",
                (event_id, company.name, company.role.value),
            )

    def _add_source(self, conn, event_id: str, source_name: str, source_url: str, confidence: float, fetched_at: str) -> None:
        """Add a source record for an event.

        Args:
            conn: Database connection.
            event_id: The event ID.
            source_name: Name of the source.
            source_url: URL of the source.
            confidence: Confidence score 0-1.
            fetched_at: ISO timestamp of fetch.
        """
        if source_name:
            conn.execute(
                """INSERT INTO event_sources (event_id, source_name, source_url, confidence, fetched_at)
                VALUES (?,?,?,?,?)""",
                (event_id, source_name, source_url, confidence, fetched_at),
            )

    def update_status(self, event_id: str, new_status: str) -> bool:
        """Update the status of an event.

        Args:
            event_id: The event ID.
            new_status: New status value.

        Returns:
            True if the event was found and updated.
        """
        conn = self.db.get_connection()
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "UPDATE events SET status=?, last_updated=? WHERE id=?",
            (new_status, now, event_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_event_by_id(self, event_id: str) -> Optional[EventResponse]:
        """Fetch a single event by ID with all related data.

        Args:
            event_id: The event ID.

        Returns:
            EventResponse or None if not found.
        """
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if not row:
            return None
        return self._row_to_response(conn, row)

    def list_events(
        self,
        search: str = "",
        category: str = "",
        continent: str = "",
        country: str = "",
        state_province: str = "",
        city: str = "",
        status: str = "",
        format_: str = "",
        organizer: str = "",
        company: str = "",
        start_date_from: str = "",
        start_date_to: str = "",
        end_date_from: str = "",
        end_date_to: str = "",
        min_audience_size: Optional[int] = None,
        max_audience_size: Optional[int] = None,
        sort_by: str = "networkingRelevance",
        sort_order: str = "desc",
    ) -> list[EventResponse]:
        """List events with filtering and sorting.

        Args:
            search: Free-text search across name, organizer, description.
            category: Filter by category.
            continent: Filter by continent.
            country: Filter by country.
            state_province: Filter by state/province.
            city: Filter by city.
            status: Filter by status.
            format_: Filter by format.
            organizer: Filter by organizer.
            company: Filter by company name.
            start_date_from: Min start date (ISO).
            start_date_to: Max start date (ISO).
            end_date_from: Min end date (ISO).
            end_date_to: Max end date (ISO).
            min_audience_size: Min audience size.
            max_audience_size: Max audience size.
            sort_by: Sort field name.
            sort_order: 'asc' or 'desc'.

        Returns:
            List of EventResponse objects.
        """
        conn = self.db.get_connection()

        query = """
            SELECT e.* FROM events e
            LEFT JOIN event_locations l ON e.id = l.event_id
        """
        conditions = []
        params: list = []

        # Exclude completed events by default
        conditions.append("LOWER(e.status) != 'completed'")
        # Exclude events whose end_date is in the past
        conditions.append("(e.end_date = '' OR e.end_date >= date('now'))")

        if search:
            conditions.append(
                "(LOWER(e.name) LIKE ? OR LOWER(e.organizer) LIKE ? OR LOWER(e.brief_description) LIKE ?)"
            )
            term = f"%{search.lower()}%"
            params.extend([term, term, term])

        if category:
            vals = [v.strip() for v in category.split(",") if v.strip()]
            if len(vals) == 1:
                conditions.append("LOWER(e.category) = LOWER(?)")
                params.append(vals[0])
            else:
                placeholders = ",".join(["LOWER(?)" for _ in vals])
                conditions.append(f"LOWER(e.category) IN ({placeholders})")
                params.extend(vals)

        if continent:
            conditions.append("LOWER(l.continent) = LOWER(?)")
            params.append(continent)

        if country:
            vals = [v.strip() for v in country.split(",") if v.strip()]
            if len(vals) == 1:
                conditions.append("LOWER(l.country) = LOWER(?)")
                params.append(vals[0])
            else:
                placeholders = ",".join(["LOWER(?)" for _ in vals])
                conditions.append(f"LOWER(l.country) IN ({placeholders})")
                params.extend(vals)

        if state_province:
            conditions.append("LOWER(l.state_province) = LOWER(?)")
            params.append(state_province)

        if city:
            conditions.append("LOWER(l.city) = LOWER(?)")
            params.append(city)

        if status:
            vals = [v.strip() for v in status.split(",") if v.strip()]
            if len(vals) == 1:
                conditions.append("LOWER(e.status) = LOWER(?)")
                params.append(vals[0])
            else:
                placeholders = ",".join(["LOWER(?)" for _ in vals])
                conditions.append(f"LOWER(e.status) IN ({placeholders})")
                params.extend(vals)

        if format_:
            vals = [v.strip() for v in format_.split(",") if v.strip()]
            if len(vals) == 1:
                conditions.append("LOWER(e.format) = LOWER(?)")
                params.append(vals[0])
            else:
                placeholders = ",".join(["LOWER(?)" for _ in vals])
                conditions.append(f"LOWER(e.format) IN ({placeholders})")
                params.extend(vals)

        if organizer:
            conditions.append("LOWER(e.organizer) LIKE LOWER(?)")
            params.append(f"%{organizer}%")

        if start_date_from:
            conditions.append("e.start_date >= ?")
            params.append(start_date_from)

        if start_date_to:
            conditions.append("e.start_date <= ?")
            params.append(start_date_to)

        if end_date_from:
            conditions.append("e.end_date >= ?")
            params.append(end_date_from)

        if end_date_to:
            conditions.append("e.end_date <= ?")
            params.append(end_date_to)

        if min_audience_size is not None:
            conditions.append("e.expected_audience_size >= ?")
            params.append(min_audience_size)

        if max_audience_size is not None:
            conditions.append("e.expected_audience_size <= ?")
            params.append(max_audience_size)

        if company:
            conditions.append(
                "e.id IN (SELECT event_id FROM event_companies WHERE LOWER(name) LIKE LOWER(?))"
            )
            params.append(f"%{company}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_map = {
            "networkingRelevance": "e.networking_relevance_score",
            "startDate": "e.start_date",
            "audienceSize": "e.expected_audience_size",
            "companiesCount": "(SELECT COUNT(*) FROM event_companies WHERE event_id = e.id)",
            "lastUpdated": "e.last_updated",
        }
        sort_col = sort_map.get(sort_by, "e.networking_relevance_score")
        direction = "ASC" if sort_order == "asc" else "DESC"
        query += f" ORDER BY {sort_col} {direction}"
        query += " LIMIT 500"

        rows = conn.execute(query, params).fetchall()
        return [self._row_to_response(conn, row) for row in rows]

    def get_all_event_ids_and_urls(self) -> list[dict]:
        """Get all event IDs, names, and URLs for status refresh.

        Returns:
            List of dicts with id, name, official_website_url, status.
        """
        conn = self.db.get_connection()
        rows = conn.execute(
            "SELECT id, name, official_website_url, status FROM events"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_event_count(self) -> int:
        """Get total number of events.

        Returns:
            Count of events in the database.
        """
        conn = self.db.get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM events").fetchone()
        return row["cnt"]

    def _row_to_response(self, conn, row) -> EventResponse:
        """Convert a database row to an EventResponse.

        Args:
            conn: Database connection.
            row: SQLite Row object from events table.

        Returns:
            EventResponse matching the frontend contract.
        """
        event_id = row["id"]

        loc_row = conn.execute(
            "SELECT * FROM event_locations WHERE event_id=?", (event_id,)
        ).fetchone()

        location = {
            "venueName": loc_row["venue_name"] if loc_row else "",
            "fullStreetAddress": loc_row["full_street_address"] if loc_row else "",
            "city": loc_row["city"] if loc_row else "",
            "stateProvince": loc_row["state_province"] if loc_row else "",
            "country": loc_row["country"] if loc_row else "",
            "postalCode": loc_row["postal_code"] if loc_row else "",
        }

        company_rows = conn.execute(
            "SELECT name, role FROM event_companies WHERE event_id=?", (event_id,)
        ).fetchall()
        companies = [{"name": c["name"], "role": c["role"]} for c in company_rows]

        return EventResponse(
            id=row["id"],
            name=row["name"],
            location=location,
            startDate=row["start_date"],
            endDate=row["end_date"],
            durationDays=row["duration_days"],
            organizer=row["organizer"],
            category=row["category"],
            format=row["format"],
            companiesInvolved=companies,
            expectedAudienceSize=row["expected_audience_size"],
            status=row["status"],
            officialWebsiteUrl=row["official_website_url"],
            briefDescription=row["brief_description"],
            networkingRelevanceScore=row["networking_relevance_score"],
            lastUpdated=row["last_updated"],
        )
