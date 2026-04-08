"""Ticketmaster Discovery API source adapter."""

import logging
from datetime import datetime, timedelta

import httpx

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource

logger = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

CLASSIFICATION_MAP = {
    "technology": EventCategory.TECHNOLOGY,
    "science": EventCategory.TECHNOLOGY,
    "business": EventCategory.BUSINESS,
    "finance": EventCategory.BANKING_FINANCIAL,
    "health": EventCategory.MEDICAL,
    "agriculture": EventCategory.AGRIBUSINESS,
}

SEARCH_KEYWORDS = [
    "conference",
    "summit",
    "expo",
    "congress",
    "forum",
    "tech",
    "business",
]


class TicketmasterSource(BaseEventSource):
    """Fetches events from the Ticketmaster Discovery API."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    @property
    def name(self) -> str:
        return "ticketmaster"

    def fetch_events(self) -> list[EventCreate]:
        if not settings.ticketmaster_api_key:
            logger.warning("TICKETMASTER_API_KEY not set, skipping source")
            return []

        all_events: list[EventCreate] = []
        now = datetime.utcnow()
        end = now + timedelta(days=180)

        for keyword in SEARCH_KEYWORDS:
            try:
                events = self._search(keyword, now, end)
                all_events.extend(events)
            except Exception as exc:
                logger.warning("Ticketmaster search '%s' failed: %s", keyword, exc)

        logger.info("Ticketmaster: fetched %d events total", len(all_events))
        return all_events

    def _search(self, keyword: str, start: datetime, end: datetime) -> list[EventCreate]:
        params = {
            "apikey": settings.ticketmaster_api_key,
            "keyword": keyword,
            "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "size": 100,
            "sort": "date,asc",
        }

        response = self._client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        embedded = data.get("_embedded", {})
        raw_events = embedded.get("events", [])

        results = []
        for raw in raw_events:
            parsed = self._parse_event(raw)
            if parsed:
                results.append(parsed)

        return results

    def _parse_event(self, raw: dict) -> EventCreate | None:
        try:
            name = raw.get("name", "")
            if not name:
                return None

            dates = raw.get("dates", {}).get("start", {})
            start_date = dates.get("localDate", "")
            end_date = raw.get("dates", {}).get("end", {}).get("localDate", start_date)

            venues = raw.get("_embedded", {}).get("venues", [{}])
            venue = venues[0] if venues else {}
            venue_name = venue.get("name", "")
            city = venue.get("city", {}).get("name", "")
            state = venue.get("state", {}).get("name", "")
            country = venue.get("country", {}).get("name", "")
            postal = venue.get("postalCode", "")
            address = venue.get("address", {}).get("line1", "")
            lat = None
            lng = None
            loc_data = venue.get("location", {})
            if loc_data:
                lat = float(loc_data.get("latitude", 0)) or None
                lng = float(loc_data.get("longitude", 0)) or None

            classifications = raw.get("classifications", [{}])
            segment = (classifications[0].get("segment", {}).get("name", "") if classifications else "").lower()
            genre = (classifications[0].get("genre", {}).get("name", "") if classifications else "").lower()
            category = EventCategory.TECHNOLOGY
            for key, cat in CLASSIFICATION_MAP.items():
                if key in segment or key in genre:
                    category = cat
                    break

            url = raw.get("url", "")
            info = raw.get("info", "") or raw.get("pleaseNote", "") or ""

            return EventCreate(
                name=name,
                organizer=raw.get("promoter", {}).get("name", "Unknown"),
                category=category,
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=url,
                brief_description=info[:500],
                start_date=start_date,
                end_date=end_date or start_date,
                location=LocationModel(
                    venue_name=venue_name,
                    full_street_address=address,
                    city=city,
                    state_province=state,
                    country=country,
                    postal_code=postal,
                    latitude=lat,
                    longitude=lng,
                ),
                companies=[],
                source_url=url,
                source_name="ticketmaster",
                source_confidence=0.80,
            )
        except Exception as exc:
            logger.debug("Failed to parse Ticketmaster event: %s", exc)
            return None

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
