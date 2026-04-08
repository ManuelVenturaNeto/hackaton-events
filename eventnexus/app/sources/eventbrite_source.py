"""Eventbrite API source adapter.

Deep search strategy:
- Iterates over countries across Americas, Europe, Asia, Oceania
- Searches each country with multiple keyword queries
- 365-day search window
"""

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

BASE_URL = "https://www.eventbriteapi.com/v3"

SEARCH_KEYWORDS = [
    "technology conference",
    "business summit",
    "tech expo",
    "fintech conference",
    "healthcare congress",
    "innovation forum",
    "startup event",
    "agribusiness expo",
]

COUNTRIES_AMERICAS = [
    "Brazil", "United States", "Canada", "Mexico", "Argentina",
    "Chile", "Colombia", "Peru",
]
COUNTRIES_EUROPE = [
    "United Kingdom", "Germany", "France", "Spain", "Portugal",
    "Italy", "Netherlands", "Switzerland", "Sweden", "Ireland",
]
COUNTRIES_ASIA_OCEANIA = [
    "Japan", "Singapore", "Australia", "New Zealand",
    "South Korea", "India", "United Arab Emirates",
]

ALL_COUNTRIES = COUNTRIES_AMERICAS + COUNTRIES_EUROPE + COUNTRIES_ASIA_OCEANIA


class EventbriteSource(BaseEventSource):
    """Fetches events from the Eventbrite API with deep search."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    @property
    def name(self) -> str:
        return "eventbrite"

    def fetch_events(self) -> list[EventCreate]:
        if not settings.eventbrite_api_token:
            logger.warning("EVENTBRITE_API_TOKEN not set, skipping source")
            return []

        all_events: list[EventCreate] = []
        now = datetime.utcnow()
        end = now + timedelta(days=settings.search_days_ahead)
        headers = {"Authorization": f"Bearer {settings.eventbrite_api_token}"}

        for country in ALL_COUNTRIES:
            for keyword in SEARCH_KEYWORDS:
                try:
                    params = {
                        "q": keyword,
                        "location.address": country,
                        "start_date.range_start": now.strftime("%Y-%m-%dT%H:%M:%S"),
                        "start_date.range_end": end.strftime("%Y-%m-%dT%H:%M:%S"),
                        "expand": "venue,organizer",
                    }
                    response = self._client.get(
                        f"{BASE_URL}/events/search/",
                        params=params,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()

                    for raw in data.get("events", []):
                        parsed = self._parse_event(raw)
                        if parsed:
                            all_events.append(parsed)
                except Exception as exc:
                    logger.warning(
                        "Eventbrite '%s' in %s failed: %s", keyword, country, exc
                    )

        logger.info("Eventbrite: fetched %d events total", len(all_events))
        return all_events

    def _parse_event(self, raw: dict) -> EventCreate | None:
        try:
            name = raw.get("name", {}).get("text", "")
            if not name:
                return None

            description = raw.get("description", {}).get("text", "") or ""
            url = raw.get("url", "")

            start = raw.get("start", {})
            end = raw.get("end", {})
            start_date = start.get("local", "")[:10] if start.get("local") else ""
            end_date = end.get("local", "")[:10] if end.get("local") else start_date

            venue = raw.get("venue", {}) or {}
            address = venue.get("address", {}) or {}
            city = address.get("city", "")
            state = address.get("region", "")
            country = address.get("country", "")
            lat = float(address.get("latitude", 0)) or None
            lng = float(address.get("longitude", 0)) or None

            organizer = raw.get("organizer", {}) or {}
            organizer_name = organizer.get("name", "Unknown")

            capacity = raw.get("capacity", 0) or 0

            is_online = raw.get("online_event", False)
            event_format = EventFormat.ONLINE if is_online else EventFormat.IN_PERSON

            category = self._infer_category(name, description)

            return EventCreate(
                name=name,
                organizer=organizer_name,
                category=category,
                format=event_format,
                status=EventStatus.UPCOMING,
                expected_audience_size=capacity,
                official_website_url=url,
                brief_description=description[:500],
                start_date=start_date,
                end_date=end_date,
                location=LocationModel(
                    venue_name=venue.get("name", ""),
                    full_street_address=address.get("localized_address_display", ""),
                    city=city,
                    state_province=state,
                    country=country,
                    latitude=lat,
                    longitude=lng,
                ),
                companies=[],
                source_url=url,
                source_name="eventbrite",
                source_confidence=0.80,
            )
        except Exception as exc:
            logger.debug("Failed to parse Eventbrite event: %s", exc)
            return None

    def _infer_category(self, name: str, description: str) -> EventCategory:
        text = (name + " " + description).lower()
        if any(kw in text for kw in ["bank", "financ", "fintech", "payment", "money"]):
            return EventCategory.BANKING_FINANCIAL
        if any(kw in text for kw in ["agri", "farm", "crop", "agriculture"]):
            return EventCategory.AGRIBUSINESS
        if any(kw in text for kw in ["health", "medical", "pharma", "hospital"]):
            return EventCategory.MEDICAL
        if any(kw in text for kw in ["business", "entrepreneur", "startup", "retail"]):
            return EventCategory.BUSINESS
        return EventCategory.TECHNOLOGY

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
