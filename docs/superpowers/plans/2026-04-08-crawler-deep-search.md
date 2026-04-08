# Crawler Deep Search — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand all 4 crawlers to search 365 days ahead, across all Brazilian states, Americas, Europe, Asia, and Oceania — with deep pagination/search.

**Architecture:** Each source file gets expanded search parameters. Ticketmaster iterates per country code + keyword. Eventbrite iterates per country + keyword. Sympla iterates per Brazilian state + category. Web scraper adds 10times.com URLs per country/region. Config gets a `search_days_ahead` setting (default 365).

**Tech Stack:** Same (httpx, BeautifulSoup, psycopg2). No new dependencies.

**IMPORTANT RULE:** Each task ends with a git commit to main and push to remote.

---

## Changes Summary

| File | Change |
|------|--------|
| `app/config.py` | Add `search_days_ahead: int = 365` |
| `app/sources/ticketmaster_source.py` | 365 days, iterate per country code + keyword with pagination |
| `app/sources/eventbrite_source.py` | 365 days, iterate per country + keyword |
| `app/sources/sympla_scraper.py` | Iterate per state (27 UFs) + category |
| `app/sources/web_search_source.py` | Add URLs per country/region (Americas, Europe, Asia, Oceania) |

---

### Task 1: Config — Add search_days_ahead

**Files:**
- Modify: `eventnexus/app/config.py`

- [ ] **Step 1: Add search_days_ahead to Settings**

In `eventnexus/app/config.py`, add `search_days_ahead: int = 365` to the Settings class, after `request_timeout_seconds`:

```python
"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/eventnexus"
    ticketmaster_api_key: str = ""
    eventbrite_api_token: str = ""
    max_concurrent_fetches: int = 10
    request_timeout_seconds: int = 30
    search_days_ahead: int = 365
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]


settings = Settings()
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/config.py
git commit -m "feat(crawler): add search_days_ahead config (default 365)"
git push origin main
```

---

### Task 2: Ticketmaster — Deep Search per Country + Pagination

**Files:**
- Modify: `eventnexus/app/sources/ticketmaster_source.py`

- [ ] **Step 1: Replace ticketmaster_source.py**

Replace the entire content of `eventnexus/app/sources/ticketmaster_source.py` with:

```python
"""Ticketmaster Discovery API source adapter.

Deep search strategy:
- Iterates over country codes across Americas, Europe, Asia, Oceania
- Searches each country with multiple keywords
- Paginates up to 5 pages per keyword+country (max 200 events per combo)
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
    "innovation",
    "fintech",
    "healthcare",
]

# Ticketmaster country codes
# Americas
COUNTRY_CODES_AMERICAS = [
    "BR", "US", "CA", "MX", "AR", "CL", "CO", "PE",
]
# Europe
COUNTRY_CODES_EUROPE = [
    "GB", "DE", "FR", "ES", "PT", "IT", "NL", "CH", "AT", "BE",
    "SE", "NO", "DK", "FI", "IE", "PL", "CZ",
]
# Asia + Oceania
COUNTRY_CODES_ASIA_OCEANIA = [
    "JP", "SG", "AU", "NZ", "KR", "IN", "AE",
]

ALL_COUNTRY_CODES = COUNTRY_CODES_AMERICAS + COUNTRY_CODES_EUROPE + COUNTRY_CODES_ASIA_OCEANIA

MAX_PAGES = 5


class TicketmasterSource(BaseEventSource):
    """Fetches events from the Ticketmaster Discovery API with deep search."""

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
        end = now + timedelta(days=settings.search_days_ahead)

        for country_code in ALL_COUNTRY_CODES:
            for keyword in SEARCH_KEYWORDS:
                try:
                    events = self._search_paginated(keyword, country_code, now, end)
                    all_events.extend(events)
                except Exception as exc:
                    logger.warning(
                        "Ticketmaster '%s' in %s failed: %s", keyword, country_code, exc
                    )

        logger.info("Ticketmaster: fetched %d events total", len(all_events))
        return all_events

    def _search_paginated(
        self, keyword: str, country_code: str, start: datetime, end: datetime
    ) -> list[EventCreate]:
        results: list[EventCreate] = []

        for page in range(MAX_PAGES):
            params = {
                "apikey": settings.ticketmaster_api_key,
                "keyword": keyword,
                "countryCode": country_code,
                "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "size": 200,
                "page": page,
                "sort": "date,asc",
            }

            response = self._client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            embedded = data.get("_embedded", {})
            raw_events = embedded.get("events", [])

            if not raw_events:
                break

            for raw in raw_events:
                parsed = self._parse_event(raw)
                if parsed:
                    results.append(parsed)

            # Check if there are more pages
            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 0)
            if page + 1 >= total_pages:
                break

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
            segment = (
                classifications[0].get("segment", {}).get("name", "")
                if classifications
                else ""
            ).lower()
            genre = (
                classifications[0].get("genre", {}).get("name", "")
                if classifications
                else ""
            ).lower()
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
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.ticketmaster_source import TicketmasterSource, ALL_COUNTRY_CODES
print(f'OK: {len(ALL_COUNTRY_CODES)} countries, source={TicketmasterSource().name}')
"
```
Expected: `OK: 32 countries, source=ticketmaster`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/ticketmaster_source.py
git commit -m "feat(crawler): Ticketmaster deep search — 32 countries, pagination, 365 days"
git push origin main
```

---

### Task 3: Eventbrite — Deep Search per Country + Keyword

**Files:**
- Modify: `eventnexus/app/sources/eventbrite_source.py`

- [ ] **Step 1: Replace eventbrite_source.py**

Replace the entire content of `eventnexus/app/sources/eventbrite_source.py` with:

```python
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

# Countries to search
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
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.eventbrite_source import EventbriteSource, ALL_COUNTRIES
print(f'OK: {len(ALL_COUNTRIES)} countries, source={EventbriteSource().name}')
"
```
Expected: `OK: 25 countries, source=eventbrite`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/eventbrite_source.py
git commit -m "feat(crawler): Eventbrite deep search — 25 countries, 8 keywords, 365 days"
git push origin main
```

---

### Task 4: Sympla — All 27 Brazilian States + All Categories

**Files:**
- Modify: `eventnexus/app/sources/sympla_scraper.py`

- [ ] **Step 1: Replace sympla_scraper.py**

Replace the entire content of `eventnexus/app/sources/sympla_scraper.py` with:

```python
"""Sympla web scraper source adapter.

Deep search strategy:
- Iterates over all 27 Brazilian states (UFs)
- Searches each state across all event categories
- Parses event cards from listing pages
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import httpx
from bs4 import BeautifulSoup

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

# All 27 Brazilian states (UF codes used in Sympla URLs)
BRAZILIAN_STATES = [
    ("ac", "Acre"), ("al", "Alagoas"), ("ap", "Amapá"), ("am", "Amazonas"),
    ("ba", "Bahia"), ("ce", "Ceará"), ("df", "Distrito Federal"),
    ("es", "Espírito Santo"), ("go", "Goiás"), ("ma", "Maranhão"),
    ("mt", "Mato Grosso"), ("ms", "Mato Grosso do Sul"),
    ("mg", "Minas Gerais"), ("pa", "Pará"), ("pb", "Paraíba"),
    ("pr", "Paraná"), ("pe", "Pernambuco"), ("pi", "Piauí"),
    ("rj", "Rio de Janeiro"), ("rn", "Rio Grande do Norte"),
    ("rs", "Rio Grande do Sul"), ("ro", "Rondônia"), ("rr", "Roraima"),
    ("sc", "Santa Catarina"), ("sp", "São Paulo"), ("se", "Sergipe"),
    ("to", "Tocantins"),
]

SYMPLA_CATEGORIES = [
    ("tecnologia-inovacao", EventCategory.TECHNOLOGY),
    ("negocios-empreendedorismo", EventCategory.BUSINESS),
    ("saude-bem-estar", EventCategory.MEDICAL),
    ("gastronomia-bebidas", EventCategory.BUSINESS),
    ("congressos-seminarios", EventCategory.TECHNOLOGY),
]


def _build_sympla_urls() -> list[dict]:
    """Generate all Sympla URLs: state x category."""
    urls = []
    for uf_code, state_name in BRAZILIAN_STATES:
        for cat_slug, category in SYMPLA_CATEGORIES:
            urls.append({
                "url": f"https://www.sympla.com.br/eventos/{cat_slug}-{uf_code}",
                "name": f"sympla_{uf_code}_{cat_slug}",
                "category": category,
                "state": state_name,
                "uf": uf_code.upper(),
            })
    return urls


SYMPLA_URLS = _build_sympla_urls()


class SymplaScraperSource(BaseEventSource):
    """Scrapes event listings from Sympla across all Brazilian states."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; EventNexus/1.0)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "pt-BR,pt;q=0.9",
            },
        )

    @property
    def name(self) -> str:
        return "sympla"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        def fetch_single(source: dict) -> list[EventCreate]:
            try:
                response = self._client.get(source["url"])
                response.raise_for_status()
                return self._parse_page(response.text, source)
            except Exception as exc:
                logger.debug("Sympla %s failed: %s", source["name"], exc)
                return []

        with ThreadPoolExecutor(max_workers=settings.max_concurrent_fetches) as executor:
            futures = {
                executor.submit(fetch_single, src): src for src in SYMPLA_URLS
            }
            for future in as_completed(futures):
                src = futures[future]
                try:
                    events = future.result()
                    if events:
                        all_events.extend(events)
                        logger.info("Sympla %s: %d events", src["name"], len(events))
                except Exception as exc:
                    logger.debug("Sympla %s error: %s", src["name"], exc)

        logger.info("Sympla: fetched %d events from %d URLs", len(all_events), len(SYMPLA_URLS))
        return all_events

    def _parse_page(self, html: str, source: dict) -> list[EventCreate]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        cards = soup.select(
            "[class*='event-card'], [class*='EventCard'], "
            "[class*='event-item'], a[href*='/evento/']"
        )

        for card in cards[:50]:
            event = self._parse_card(card, source)
            if event:
                events.append(event)

        return events

    def _parse_card(self, card, source: dict) -> Optional[EventCreate]:
        try:
            name_el = card.select_one("h3, h2, h4, [class*='title'], [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                return None

            date_el = card.select_one("[class*='date'], time, [class*='when']")
            date_text = date_el.get_text(strip=True) if date_el else ""
            start_date, end_date = self._parse_dates(date_text)

            loc_el = card.select_one("[class*='location'], [class*='venue'], [class*='where']")
            location_text = loc_el.get_text(strip=True) if loc_el else ""

            link = card.get("href") or ""
            if not link:
                a = card.select_one("a[href]")
                link = a.get("href", "") if a else ""
            if link and not link.startswith("http"):
                link = f"https://www.sympla.com.br{link}"

            city = ""
            if location_text:
                parts = [p.strip() for p in location_text.split(",")]
                city = parts[0] if parts else ""

            return EventCreate(
                name=name,
                organizer="Unknown",
                category=source["category"],
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=link,
                brief_description="",
                start_date=start_date,
                end_date=end_date or start_date,
                location=LocationModel(
                    city=city,
                    state_province=source.get("state", ""),
                    country="Brazil",
                    continent="South America",
                ),
                companies=[],
                source_url=source["url"],
                source_name="sympla",
                source_confidence=0.50,
            )
        except Exception as exc:
            logger.debug("Failed to parse Sympla card: %s", exc)
            return None

    def _parse_dates(self, text: str) -> tuple[str, str]:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if len(dates) >= 2:
            return dates[0], dates[1]
        if len(dates) == 1:
            return dates[0], dates[0]
        return "", ""

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.sympla_scraper import SymplaScraperSource, SYMPLA_URLS, BRAZILIAN_STATES
print(f'OK: {len(BRAZILIAN_STATES)} states, {len(SYMPLA_URLS)} URLs, source={SymplaScraperSource().name}')
"
```
Expected: `OK: 27 states, 135 URLs, source=sympla`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/sympla_scraper.py
git commit -m "feat(crawler): Sympla deep search — 27 states x 5 categories, concurrent"
git push origin main
```

---

### Task 5: Web Search — Expand 10times.com per Region/Country

**Files:**
- Modify: `eventnexus/app/sources/web_search_source.py` (only the SEARCH_URLS list)

- [ ] **Step 1: Replace the SEARCH_URLS list**

In `eventnexus/app/sources/web_search_source.py`, replace the `SEARCH_URLS` list (lines 47-78) with:

```python
# Known event listing URLs for scraping — deep search across regions
_CATEGORIES_10TIMES = ["technology", "banking-finance", "agriculture", "medical-pharma", "business"]

# Countries per region for 10times.com
_COUNTRIES_AMERICAS = ["brazil", "united-states", "canada", "mexico", "argentina", "chile", "colombia"]
_COUNTRIES_EUROPE = ["united-kingdom", "germany", "france", "spain", "portugal", "italy", "netherlands", "switzerland"]
_COUNTRIES_ASIA_OCEANIA = ["japan", "singapore", "australia", "india", "south-korea", "uae"]

_ALL_COUNTRIES = _COUNTRIES_AMERICAS + _COUNTRIES_EUROPE + _COUNTRIES_ASIA_OCEANIA


def _build_search_urls() -> list[dict]:
    urls = []
    # 10times: per country per category
    for country in _ALL_COUNTRIES:
        for category in _CATEGORIES_10TIMES:
            urls.append({
                "url": f"https://10times.com/{country}/{category}",
                "name": f"10times_{country}_{category}",
                "region": country,
            })
    # Global aggregators
    urls.append({"url": "https://10times.com/technology/conferences", "name": "10times_global_tech", "region": "global"})
    urls.append({"url": "https://confs.tech/", "name": "confs_tech", "region": "global"})
    return urls


SEARCH_URLS: list[dict] = _build_search_urls()
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.web_search_source import WebSearchSource, SEARCH_URLS
print(f'OK: {len(SEARCH_URLS)} URLs, source={WebSearchSource().name}')
"
```
Expected: `OK: 107 URLs, source=web_search` (21 countries x 5 categories + 2 global = 107)

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/web_search_source.py
git commit -m "feat(crawler): web search deep — 21 countries x 5 categories on 10times.com"
git push origin main
```

---

## Summary

| Task | Source | Before | After |
|------|--------|--------|-------|
| 1 | Config | 180 days hardcoded | `search_days_ahead=365` configurable |
| 2 | Ticketmaster | 7 keywords, no country filter | 10 keywords x 32 countries, pagination (5 pages) |
| 3 | Eventbrite | 5 queries, Brazil only | 8 keywords x 25 countries |
| 4 | Sympla | 3 category URLs | 27 states x 5 categories = 135 URLs, concurrent |
| 5 | Web Search | 6 URLs | 21 countries x 5 categories + 2 global = 107 URLs |

**Total search combinations:** ~920 (vs ~21 before) — ~44x more coverage.
