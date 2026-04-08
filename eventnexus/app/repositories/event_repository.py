"""Repository for event CRUD operations on PostgreSQL."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import Database
from app.models.event import (
    CompanyResponse,
    EventCreate,
    EventResponse,
    LocationModel,
    LocationResponse,
    SourceResponse,
    CompanyModel,
)

logger = logging.getLogger(__name__)


class EventRepository:
    """Handles all event persistence operations against PostgreSQL."""

    def __init__(self, database: Database) -> None:
        self.db = database

    def _generate_dedup_key(self, event: EventCreate) -> str:
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

        Returns:
            Tuple of (event_id, was_inserted).
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        dedup_key = self._generate_dedup_key(event)

        cur.execute("SELECT id FROM events WHERE dedup_key = %s", (dedup_key,))
        existing = cur.fetchone()

        if existing:
            event_id = str(existing["id"])
            cur.execute(
                """UPDATE events SET
                    name=%s, organizer=%s, category=%s, format=%s, status=%s,
                    expected_audience_size=%s, official_website_url=%s,
                    brief_description=%s, networking_relevance_score=%s,
                    start_date=%s, end_date=%s, duration_days=%s, last_updated=%s
                WHERE id=%s""",
                (
                    event.name, event.organizer, event.category.value,
                    event.format.value, event.status.value,
                    event.expected_audience_size, event.official_website_url,
                    event.brief_description, event.networking_relevance_score,
                    event.start_date or None, event.end_date or None,
                    event.duration_days, now, event_id,
                ),
            )
            self._upsert_location(cur, event_id, event.location)
            self._replace_companies(cur, event_id, event.companies)
            self._add_source(cur, event_id, event.source_name, event.source_url, event.source_confidence, now)
            conn.commit()
            return event_id, False

        event_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO events
                (id, name, organizer, category, format, status,
                 expected_audience_size, official_website_url,
                 brief_description, networking_relevance_score,
                 start_date, end_date, duration_days,
                 last_updated, created_at, dedup_key)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id, event.name, event.organizer, event.category.value,
                event.format.value, event.status.value,
                event.expected_audience_size, event.official_website_url,
                event.brief_description, event.networking_relevance_score,
                event.start_date or None, event.end_date or None,
                event.duration_days, now, now, dedup_key,
            ),
        )
        self._upsert_location(cur, event_id, event.location)
        self._replace_companies(cur, event_id, event.companies)
        self._add_source(cur, event_id, event.source_name, event.source_url, event.source_confidence, now)
        conn.commit()
        return event_id, True

    def _upsert_location(self, cur, event_id: str, loc: LocationModel) -> None:
        cur.execute("DELETE FROM event_locations WHERE event_id = %s", (event_id,))
        cur.execute(
            """INSERT INTO event_locations
                (event_id, venue_name, full_street_address, city, state_province,
                 country, postal_code, continent, neighborhood, street,
                 street_number, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id, loc.venue_name, loc.full_street_address, loc.city,
                loc.state_province, loc.country, loc.postal_code, loc.continent,
                loc.neighborhood, loc.street, loc.street_number,
                loc.latitude, loc.longitude,
            ),
        )

    def _replace_companies(self, cur, event_id: str, companies: list[CompanyModel]) -> None:
        cur.execute("DELETE FROM event_companies WHERE event_id = %s", (event_id,))
        for company in companies:
            cur.execute(
                "INSERT INTO event_companies (event_id, name, role) VALUES (%s,%s,%s)",
                (event_id, company.name, company.role.value),
            )

    def _add_source(self, cur, event_id: str, source_name: str, source_url: str, confidence: float, fetched_at: str) -> None:
        if source_name:
            cur.execute(
                """INSERT INTO event_sources (event_id, source_name, source_url, confidence, fetched_at)
                VALUES (%s,%s,%s,%s,%s)""",
                (event_id, source_name, source_url, confidence, fetched_at),
            )

    def update_status(self, event_id: str, new_status: str) -> bool:
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "UPDATE events SET status=%s, last_updated=%s WHERE id=%s",
            (new_status, now, event_id),
        )
        conn.commit()
        return cur.rowcount > 0

    def get_event_by_id(self, event_id: str) -> Optional[EventResponse]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_response(cur, row)

    def list_events(
        self,
        search: str = "",
        category: str = "",
        country: str = "",
        city: str = "",
        status: str = "",
        format_: str = "",
        start_date_from: str = "",
        start_date_to: str = "",
        min_audience_size: Optional[int] = None,
        sort_by: str = "networkingRelevance",
        sort_order: str = "desc",
    ) -> list[EventResponse]:
        conn = self.db.get_connection()
        cur = conn.cursor()

        query = """
            SELECT e.* FROM events e
            LEFT JOIN event_locations l ON e.id = l.event_id
        """
        conditions = []
        params: list = []

        if not status:
            conditions.append("LOWER(e.status) = 'upcoming'")
        else:
            conditions.append("LOWER(e.status) = LOWER(%s)")
            params.append(status)

        conditions.append("(e.end_date IS NULL OR e.end_date >= CURRENT_DATE)")

        if search:
            conditions.append(
                "(LOWER(e.name) LIKE %s OR LOWER(e.organizer) LIKE %s OR LOWER(e.brief_description) LIKE %s)"
            )
            term = f"%{search.lower()}%"
            params.extend([term, term, term])

        if category:
            conditions.append("LOWER(e.category) = LOWER(%s)")
            params.append(category)

        if country:
            conditions.append("LOWER(l.country) = LOWER(%s)")
            params.append(country)

        if city:
            conditions.append("LOWER(l.city) = LOWER(%s)")
            params.append(city)

        if format_:
            conditions.append("LOWER(e.format) = LOWER(%s)")
            params.append(format_)

        if start_date_from:
            conditions.append("e.start_date >= %s")
            params.append(start_date_from)

        if start_date_to:
            conditions.append("e.start_date <= %s")
            params.append(start_date_to)

        if min_audience_size is not None:
            conditions.append("e.expected_audience_size >= %s")
            params.append(min_audience_size)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_map = {
            "networkingRelevance": "e.networking_relevance_score",
            "startDate": "e.start_date",
            "audienceSize": "e.expected_audience_size",
            "lastUpdated": "e.last_updated",
        }
        sort_col = sort_map.get(sort_by, "e.networking_relevance_score")
        direction = "ASC" if sort_order == "asc" else "DESC"

        if sort_by == "networkingRelevance":
            query += f" ORDER BY {sort_col} {direction}, e.start_date ASC"
        else:
            query += f" ORDER BY {sort_col} {direction}"

        query += " LIMIT 500"

        cur.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_response(cur, row) for row in rows]

    def get_all_event_ids_and_urls(self) -> list[dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, official_website_url, status FROM events")
        return [dict(r) for r in cur.fetchall()]

    def get_event_count(self) -> int:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM events")
        return cur.fetchone()["cnt"]

    def _row_to_response(self, cur, row: dict) -> EventResponse:
        event_id = str(row["id"])

        cur.execute("SELECT * FROM event_locations WHERE event_id = %s", (event_id,))
        loc = cur.fetchone()

        location = LocationResponse(
            venueName=loc["venue_name"] if loc else "",
            fullStreetAddress=loc["full_street_address"] if loc else "",
            city=loc["city"] if loc else "",
            stateProvince=loc["state_province"] if loc else "",
            country=loc["country"] if loc else "",
            postalCode=loc["postal_code"] if loc else "",
            continent=loc["continent"] if loc else "",
            latitude=loc["latitude"] if loc else None,
            longitude=loc["longitude"] if loc else None,
        )

        cur.execute("SELECT name, role FROM event_companies WHERE event_id = %s", (event_id,))
        companies = [CompanyResponse(name=c["name"], role=c["role"]) for c in cur.fetchall()]

        cur.execute("SELECT source_name, confidence FROM event_sources WHERE event_id = %s", (event_id,))
        sources = [SourceResponse(sourceName=s["source_name"], confidence=s["confidence"]) for s in cur.fetchall()]

        return EventResponse(
            id=event_id,
            name=row["name"],
            organizer=row["organizer"] or "",
            category=row["category"] or "",
            format=row["format"] or "",
            status=row["status"] or "",
            expectedAudienceSize=row["expected_audience_size"] or 0,
            officialWebsiteUrl=row["official_website_url"] or "",
            briefDescription=row["brief_description"] or "",
            networkingRelevanceScore=row["networking_relevance_score"] or 0,
            startDate=str(row["start_date"] or ""),
            endDate=str(row["end_date"] or ""),
            durationDays=row["duration_days"] or 1,
            lastUpdated=str(row["last_updated"] or ""),
            location=location,
            companiesInvolved=companies,
            sources=sources,
        )
