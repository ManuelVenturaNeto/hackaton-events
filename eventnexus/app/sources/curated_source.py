"""Curated event source — loads pre-fetched events from JSON file.

Reads curated_events.json which contains events exported from the database.
This serves as a reliable baseline that works even when external APIs are down.
"""

import json
import logging
from pathlib import Path

from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).parent / "curated_events.json"

GLOBAL_EVENTS: list[dict] = []
BRAZIL_EVENTS: list[dict] = []

# Load events from JSON at import time
try:
    with open(_JSON_PATH, encoding="utf-8") as f:
        _all = json.load(f)
    BRAZIL_EVENTS = [e for e in _all if (e.get("location", {}).get("country", "")).lower() == "brazil"]
    GLOBAL_EVENTS = [e for e in _all if (e.get("location", {}).get("country", "")).lower() != "brazil"]
    logger.info("Loaded %d curated events from JSON (%d global, %d Brazil)",
                len(_all), len(GLOBAL_EVENTS), len(BRAZIL_EVENTS))
except FileNotFoundError:
    logger.warning("curated_events.json not found, curated source will return 0 events")
except Exception as exc:
    logger.warning("Failed to load curated_events.json: %s", exc)


_CATEGORY_MAP = {
    "Technology": EventCategory.TECHNOLOGY,
    "Banking / Financial": EventCategory.BANKING_FINANCIAL,
    "Agribusiness / Agriculture": EventCategory.AGRIBUSINESS,
    "Medical / Healthcare": EventCategory.MEDICAL,
    "Business / Entrepreneurship": EventCategory.BUSINESS,
}

_FORMAT_MAP = {
    "in-person": EventFormat.IN_PERSON,
    "hybrid": EventFormat.HYBRID,
    "online": EventFormat.ONLINE,
}

_STATUS_MAP = {
    "upcoming": EventStatus.UPCOMING,
    "canceled": EventStatus.CANCELED,
    "postponed": EventStatus.POSTPONED,
    "completed": EventStatus.COMPLETED,
}

_ROLE_MAP = {
    "organizer": CompanyRole.ORGANIZER,
    "sponsor": CompanyRole.SPONSOR,
    "exhibitor": CompanyRole.EXHIBITOR,
    "partner": CompanyRole.PARTNER,
    "featured": CompanyRole.FEATURED,
}


class CuratedEventSource(BaseEventSource):

    @property
    def name(self) -> str:
        return "curated"

    def fetch_events(self) -> list[EventCreate]:
        events = []
        for data in GLOBAL_EVENTS + BRAZIL_EVENTS:
            try:
                events.append(self._to_event_create(data))
            except Exception as exc:
                logger.debug("Skipping curated event '%s': %s", data.get("name", "?"), exc)
        logger.info("Curated source produced %d events (%d global, %d Brazil)",
                     len(events), len(GLOBAL_EVENTS), len(BRAZIL_EVENTS))
        return events

    def _to_event_create(self, data: dict) -> EventCreate:
        loc = data.get("location", {})
        companies = []
        for c in data.get("companies", []):
            role = _ROLE_MAP.get(c.get("role", ""), CompanyRole.PARTNER)
            companies.append(CompanyModel(name=c["name"], role=role))

        return EventCreate(
            name=data["name"],
            organizer=data.get("organizer", "Unknown"),
            category=_CATEGORY_MAP.get(data.get("category", ""), EventCategory.TECHNOLOGY),
            format=_FORMAT_MAP.get(data.get("format", ""), EventFormat.IN_PERSON),
            status=_STATUS_MAP.get(data.get("status", ""), EventStatus.UPCOMING),
            expected_audience_size=data.get("expected_audience_size", 0),
            official_website_url=data.get("official_website_url", ""),
            brief_description=data.get("brief_description", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            duration_days=data.get("duration_days", 1),
            location=LocationModel(
                venue_name=loc.get("venue_name", ""),
                full_street_address=loc.get("full_street_address", ""),
                city=loc.get("city", ""),
                state_province=loc.get("state_province", ""),
                country=loc.get("country", ""),
                postal_code=loc.get("postal_code", ""),
                continent=loc.get("continent", ""),
                latitude=loc.get("latitude"),
                longitude=loc.get("longitude"),
            ),
            companies=companies,
            source_url=data.get("source_url", ""),
            source_name="curated",
            source_confidence=data.get("source_confidence", 0.95),
        )

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        for data in GLOBAL_EVENTS + BRAZIL_EVENTS:
            if data["name"].lower() == event_name.lower():
                return data.get("status", "upcoming")
        return None
