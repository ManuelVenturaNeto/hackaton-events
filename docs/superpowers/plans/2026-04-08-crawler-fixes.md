# Crawler Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 4 non-curated crawlers that currently return 0 events due to API deprecation, anti-bot blocks, and client-side rendering.

**Architecture:** Add Playwright as a shared browser engine for Sympla, 10times, and Eventbrite scraping. Ticketmaster stays as HTTP API. A shared `browser_pool.py` manages a single Playwright browser instance reused across scrapers. Eventbrite switches from deprecated API to Playwright scraping of the public website.

**Tech Stack:** playwright (browser automation), existing httpx for Ticketmaster API.

**Diagnosed problems:**
| Source | Problem | Fix |
|--------|---------|-----|
| Ticketmaster | Works for US, but `classificationName` returns 0 for most categories | Keep keyword search, it works (233 events for "tech" US). Already correct. |
| Eventbrite | `/v3/events/search/` deprecated since Feb 2020, returns 404 | Scrape eventbrite.com website via Playwright |
| Sympla | React SPA, HTML has 0 event cards (client-side rendered) | Scrape via Playwright, wait for JS rendering |
| 10times | Cloudflare 403 blocks httpx requests | Scrape via Playwright (real browser bypasses Cloudflare) |

**IMPORTANT RULE:** Each task ends with a git commit to main and push to remote.

---

## File Structure (changes only)

```
eventnexus/
├── requirements.txt                      # Add: playwright
├── app/
│   ├── sources/
│   │   ├── browser_pool.py               # NEW: shared Playwright browser manager
│   │   ├── ticketmaster_source.py        # Minor fix: remove dead country codes
│   │   ├── eventbrite_source.py          # REWRITE: Playwright scraper
│   │   ├── sympla_scraper.py             # REWRITE: Playwright scraper
│   │   └── web_search_source.py          # REWRITE: Playwright for 10times
│   └── ...
└── Dockerfile                            # Add: playwright install
```

---

### Task 1: Add Playwright + Browser Pool

**Files:**
- Modify: `eventnexus/requirements.txt`
- Modify: `eventnexus/Dockerfile`
- Create: `eventnexus/app/sources/browser_pool.py`

- [ ] **Step 1: Add playwright to requirements.txt**

Add `playwright==1.52.0` at the end of `eventnexus/requirements.txt`.

- [ ] **Step 2: Install playwright and browsers**

```bash
cd /home/robson/code/hackaton/eventnexus
venv/bin/pip install playwright==1.52.0
venv/bin/playwright install chromium
```

- [ ] **Step 3: Update Dockerfile**

Replace `eventnexus/Dockerfile` with:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Playwright system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create browser_pool.py**

Create `eventnexus/app/sources/browser_pool.py`:
```python
"""Shared Playwright browser pool for web scrapers.

Manages a single Chromium browser instance reused across all scraper sources.
Uses sync Playwright API (not async) to match the existing ThreadPoolExecutor pattern.
"""

import logging
from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger(__name__)

_playwright = None
_browser = None


def get_browser() -> Browser:
    """Get or create the shared Playwright browser instance."""
    global _playwright, _browser
    if _browser is None or not _browser.is_connected():
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Playwright browser launched")
    return _browser


def new_page() -> Page:
    """Create a new browser page with standard settings."""
    browser = get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        locale="pt-BR",
        viewport={"width": 1280, "height": 720},
    )
    return context.new_page()


def close_browser() -> None:
    """Close the shared browser instance."""
    global _playwright, _browser
    if _browser:
        _browser.close()
        _browser = None
    if _playwright:
        _playwright.stop()
        _playwright = None
```

- [ ] **Step 5: Verify playwright works**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.browser_pool import new_page, close_browser
page = new_page()
page.goto('https://example.com')
print(f'OK: title={page.title()}')
page.close()
close_browser()
"
```
Expected: `OK: title=Example Domain`

- [ ] **Step 6: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/requirements.txt eventnexus/Dockerfile eventnexus/app/sources/browser_pool.py
git commit -m "feat(crawler): add Playwright browser pool for JS-rendered scrapers"
git push origin main
```

---

### Task 2: Fix Ticketmaster — Focus on Productive Countries

**Files:**
- Modify: `eventnexus/app/sources/ticketmaster_source.py`

The Ticketmaster API works but most countries return 0 for professional event keywords. Testing showed US returns data (233 for "tech", 275 for "expo", 158 for "summit"), GB/DE/AU return near-zero. The fix: reduce country list to those that actually have Ticketmaster coverage for business/tech events, and add more keyword variations.

- [ ] **Step 1: Update country codes and keywords**

In `eventnexus/app/sources/ticketmaster_source.py`, replace the country code lists and keywords:

Replace:
```python
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
COUNTRY_CODES_AMERICAS = [
    "BR", "US", "CA", "MX", "AR", "CL", "CO", "PE",
]
COUNTRY_CODES_EUROPE = [
    "GB", "DE", "FR", "ES", "PT", "IT", "NL", "CH", "AT", "BE",
    "SE", "NO", "DK", "FI", "IE", "PL", "CZ",
]
COUNTRY_CODES_ASIA_OCEANIA = [
    "JP", "SG", "AU", "NZ", "KR", "IN", "AE",
]

ALL_COUNTRY_CODES = COUNTRY_CODES_AMERICAS + COUNTRY_CODES_EUROPE + COUNTRY_CODES_ASIA_OCEANIA
```

With:
```python
SEARCH_KEYWORDS = [
    "tech",
    "conference",
    "summit",
    "expo",
    "congress",
    "forum",
    "business",
    "innovation",
    "startup",
    "digital",
    "AI",
    "cloud",
    "fintech",
    "healthcare",
    "agribusiness",
]

# Only countries with meaningful Ticketmaster coverage for business/tech
ALL_COUNTRY_CODES = [
    "US", "CA", "MX", "GB", "AU", "NZ", "IE",
]
```

- [ ] **Step 2: Verify**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.ticketmaster_source import ALL_COUNTRY_CODES, SEARCH_KEYWORDS
print(f'OK: {len(ALL_COUNTRY_CODES)} countries, {len(SEARCH_KEYWORDS)} keywords')
"
```
Expected: `OK: 7 countries, 15 keywords`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/ticketmaster_source.py
git commit -m "fix(crawler): Ticketmaster — focus on 7 countries with actual coverage, 15 keywords"
git push origin main
```

---

### Task 3: Rewrite Eventbrite — Playwright Scraper

**Files:**
- Modify: `eventnexus/app/sources/eventbrite_source.py`

The Eventbrite Search API was deprecated in Feb 2020 and returns 404. Replace with Playwright scraping of `eventbrite.com/d/` search pages.

- [ ] **Step 1: Replace eventbrite_source.py**

Replace the entire content of `eventnexus/app/sources/eventbrite_source.py` with:

```python
"""Eventbrite source adapter — Playwright scraper.

The Eventbrite Search API (/v3/events/search/) was deprecated in Feb 2020.
This adapter scrapes the public Eventbrite search pages using Playwright
to render the JavaScript-based event listings.

Search strategy:
- Uses eventbrite.com/d/{location}/{category}/ URL pattern
- Iterates over countries and search keywords
- Parses rendered event cards from the DOM
"""

import logging
import re
from typing import Optional

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource
from app.sources.browser_pool import new_page

logger = logging.getLogger(__name__)

# Eventbrite search URL locations (country slug for /d/{slug}/)
LOCATIONS = [
    ("brazil", "Brazil"),
    ("united-states", "USA"),
    ("canada", "Canada"),
    ("mexico", "Mexico"),
    ("argentina", "Argentina"),
    ("united-kingdom", "UK"),
    ("germany", "Germany"),
    ("france", "France"),
    ("spain", "Spain"),
    ("portugal", "Portugal"),
    ("australia", "Australia"),
    ("japan", "Japan"),
    ("singapore", "Singapore"),
]

SEARCH_KEYWORDS = [
    "technology-conference",
    "business-summit",
    "tech-expo",
    "startup",
    "innovation",
]


class EventbriteSource(BaseEventSource):
    """Scrapes events from Eventbrite search pages via Playwright."""

    @property
    def name(self) -> str:
        return "eventbrite"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for loc_slug, country_name in LOCATIONS:
            for keyword in SEARCH_KEYWORDS:
                try:
                    url = f"https://www.eventbrite.com/d/{loc_slug}/{keyword}/"
                    events = self._scrape_page(url, country_name)
                    all_events.extend(events)
                    if events:
                        logger.info("Eventbrite %s/%s: %d events", loc_slug, keyword, len(events))
                except Exception as exc:
                    logger.debug("Eventbrite %s/%s failed: %s", loc_slug, keyword, exc)

        logger.info("Eventbrite: fetched %d events total", len(all_events))
        return all_events

    def _scrape_page(self, url: str, default_country: str) -> list[EventCreate]:
        page = new_page()
        events: list[EventCreate] = []
        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(2000)

            cards = page.query_selector_all(
                "[class*='event-card'], [data-testid*='event'], "
                "[class*='DiscoverHorizontalEventCard'], [class*='search-event-card'], "
                "article, [class*='eds-event-card']"
            )

            for card in cards[:30]:
                event = self._parse_card(card, url, default_country)
                if event:
                    events.append(event)
        except Exception as exc:
            logger.debug("Eventbrite page scrape failed for %s: %s", url, exc)
        finally:
            page.context.close()

        return events

    def _parse_card(self, card, source_url: str, default_country: str) -> Optional[EventCreate]:
        try:
            name_el = card.query_selector("h2, h3, [class*='title'], [class*='name']")
            name = name_el.inner_text().strip() if name_el else ""
            if not name or len(name) < 3:
                return None

            date_el = card.query_selector("[class*='date'], time, [class*='start-date']")
            date_text = date_el.inner_text().strip() if date_el else ""
            start_date = self._extract_date(date_text)

            loc_el = card.query_selector("[class*='location'], [class*='venue'], [class*='card-text--truncated']")
            location_text = loc_el.inner_text().strip() if loc_el else ""
            city = location_text.split(",")[0].strip() if location_text else ""

            link_el = card.query_selector("a[href*='eventbrite.com/e/']")
            link = link_el.get_attribute("href") if link_el else ""
            if not link:
                link_el = card.query_selector("a[href]")
                link = link_el.get_attribute("href") if link_el else ""

            desc_el = card.query_selector("[class*='desc'], [class*='summary'], p")
            description = desc_el.inner_text().strip()[:500] if desc_el else ""

            return EventCreate(
                name=name,
                organizer="Unknown",
                category=self._infer_category(name, description),
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=link,
                brief_description=description,
                start_date=start_date,
                end_date=start_date,
                location=LocationModel(
                    city=city,
                    country=default_country,
                ),
                companies=[],
                source_url=source_url,
                source_name="eventbrite",
                source_confidence=0.70,
            )
        except Exception as exc:
            logger.debug("Failed to parse Eventbrite card: %s", exc)
            return None

    def _extract_date(self, text: str) -> str:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if dates:
            return dates[0]
        return ""

    def _infer_category(self, name: str, description: str) -> EventCategory:
        text = (name + " " + description).lower()
        if any(kw in text for kw in ["bank", "financ", "fintech", "payment"]):
            return EventCategory.BANKING_FINANCIAL
        if any(kw in text for kw in ["agri", "farm", "agriculture"]):
            return EventCategory.AGRIBUSINESS
        if any(kw in text for kw in ["health", "medical", "pharma"]):
            return EventCategory.MEDICAL
        if any(kw in text for kw in ["business", "entrepreneur", "startup"]):
            return EventCategory.BUSINESS
        return EventCategory.TECHNOLOGY

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.eventbrite_source import EventbriteSource, LOCATIONS
print(f'OK: {len(LOCATIONS)} locations, source={EventbriteSource().name}')
"
```
Expected: `OK: 13 locations, source=eventbrite`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/eventbrite_source.py
git commit -m "fix(crawler): Eventbrite — rewrite as Playwright scraper (API deprecated since 2020)"
git push origin main
```

---

### Task 4: Rewrite Sympla — Playwright Scraper

**Files:**
- Modify: `eventnexus/app/sources/sympla_scraper.py`

Sympla is a React SPA — the HTML returned by httpx has zero event cards. Playwright renders the JS and gives us the actual DOM.

- [ ] **Step 1: Replace sympla_scraper.py**

Replace the entire content of `eventnexus/app/sources/sympla_scraper.py` with:

```python
"""Sympla web scraper source adapter — Playwright.

Sympla is a React SPA that requires JavaScript rendering.
Uses Playwright to load pages and extract event data from the rendered DOM.

Deep search: all 27 Brazilian states x 5 categories.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource
from app.sources.browser_pool import new_page

logger = logging.getLogger(__name__)

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
    """Scrapes Sympla event listings using Playwright for JS rendering."""

    @property
    def name(self) -> str:
        return "sympla"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for source in SYMPLA_URLS:
            try:
                events = self._scrape_page(source)
                if events:
                    all_events.extend(events)
                    logger.info("Sympla %s: %d events", source["name"], len(events))
            except Exception as exc:
                logger.debug("Sympla %s failed: %s", source["name"], exc)

        logger.info("Sympla: fetched %d events from %d URLs", len(all_events), len(SYMPLA_URLS))
        return all_events

    def _scrape_page(self, source: dict) -> list[EventCreate]:
        page = new_page()
        events: list[EventCreate] = []
        try:
            page.goto(source["url"], timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            cards = page.query_selector_all(
                "[class*='event-card'], [class*='EventCard'], "
                "[class*='event-item'], a[href*='/evento/'], "
                "[class*='sympla-card'], [data-testid*='event']"
            )

            for card in cards[:50]:
                event = self._parse_card(card, source)
                if event:
                    events.append(event)
        except Exception as exc:
            logger.debug("Sympla page scrape failed for %s: %s", source["url"], exc)
        finally:
            page.context.close()

        return events

    def _parse_card(self, card, source: dict) -> Optional[EventCreate]:
        try:
            name_el = card.query_selector("h3, h2, h4, [class*='title'], [class*='name']")
            name = name_el.inner_text().strip() if name_el else ""
            if not name or len(name) < 3:
                return None

            date_el = card.query_selector("[class*='date'], time, [class*='when']")
            date_text = date_el.inner_text().strip() if date_el else ""
            start_date, end_date = self._parse_dates(date_text)

            loc_el = card.query_selector("[class*='location'], [class*='venue'], [class*='where']")
            location_text = loc_el.inner_text().strip() if loc_el else ""
            city = location_text.split(",")[0].strip() if location_text else ""

            link = card.get_attribute("href") or ""
            if not link:
                a = card.query_selector("a[href]")
                link = a.get_attribute("href") if a else ""
            if link and not link.startswith("http"):
                link = f"https://www.sympla.com.br{link}"

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
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.sympla_scraper import SymplaScraperSource, SYMPLA_URLS
print(f'OK: {len(SYMPLA_URLS)} URLs, source={SymplaScraperSource().name}')
"
```
Expected: `OK: 135 URLs, source=sympla`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/sympla_scraper.py
git commit -m "fix(crawler): Sympla — rewrite with Playwright for JS-rendered React SPA"
git push origin main
```

---

### Task 5: Rewrite Web Search (10times) — Playwright Scraper

**Files:**
- Modify: `eventnexus/app/sources/web_search_source.py`

10times.com returns 403 via httpx due to Cloudflare. Playwright with a real Chromium browser bypasses this.

- [ ] **Step 1: Replace web_search_source.py**

Replace the entire content of `eventnexus/app/sources/web_search_source.py` with:

```python
"""Web search source adapter — Playwright scraper.

Uses Playwright to bypass Cloudflare protection on 10times.com
and render JavaScript-heavy event listing pages.

Deep search: 21 countries x 5 categories + confs.tech.
"""

import logging
import re
from typing import Optional

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource
from app.sources.browser_pool import new_page

logger = logging.getLogger(__name__)

_CATEGORIES_10TIMES = ["technology", "banking-finance", "agriculture", "medical-pharma", "business"]

_COUNTRIES_AMERICAS = ["brazil", "united-states", "canada", "mexico", "argentina", "chile", "colombia"]
_COUNTRIES_EUROPE = ["united-kingdom", "germany", "france", "spain", "portugal", "italy", "netherlands", "switzerland"]
_COUNTRIES_ASIA_OCEANIA = ["japan", "singapore", "australia", "india", "south-korea", "uae"]

_ALL_COUNTRIES = _COUNTRIES_AMERICAS + _COUNTRIES_EUROPE + _COUNTRIES_ASIA_OCEANIA


def _build_search_urls() -> list[dict]:
    urls = []
    for country in _ALL_COUNTRIES:
        for category in _CATEGORIES_10TIMES:
            urls.append({
                "url": f"https://10times.com/{country}/{category}",
                "name": f"10times_{country}_{category}",
                "region": country,
            })
    urls.append({"url": "https://10times.com/technology/conferences", "name": "10times_global_tech", "region": "global"})
    urls.append({"url": "https://confs.tech/", "name": "confs_tech", "region": "global"})
    return urls


SEARCH_URLS: list[dict] = _build_search_urls()

CONTINENT_MAP = {
    "usa": "North America", "united states": "North America", "canada": "North America",
    "mexico": "North America",
    "brazil": "South America", "argentina": "South America", "chile": "South America",
    "colombia": "South America",
    "uk": "Europe", "germany": "Europe", "france": "Europe", "spain": "Europe",
    "portugal": "Europe", "italy": "Europe", "netherlands": "Europe", "switzerland": "Europe",
    "japan": "Asia", "singapore": "Asia", "india": "Asia", "south korea": "Asia",
    "uae": "Asia", "israel": "Asia",
    "australia": "Oceania", "new zealand": "Oceania",
}


class WebSearchSource(BaseEventSource):
    """Scrapes event listing sites using Playwright for JS rendering and anti-bot bypass."""

    @property
    def name(self) -> str:
        return "web_search"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for source in SEARCH_URLS:
            try:
                events = self._scrape_page(source)
                if events:
                    all_events.extend(events)
                    logger.info("WebSearch %s: %d events", source["name"], len(events))
            except Exception as exc:
                logger.debug("WebSearch %s failed: %s", source["name"], exc)

        logger.info("WebSearch: fetched %d events from %d URLs", len(all_events), len(SEARCH_URLS))
        return all_events

    def _scrape_page(self, source: dict) -> list[EventCreate]:
        page = new_page()
        events: list[EventCreate] = []
        try:
            page.goto(source["url"], timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            cards = page.query_selector_all(
                "[class*='event-card'], [class*='event-item'], "
                "[class*='EventCard'], [class*='listing-item'], "
                "[data-type='event'], .event, .conference-item, "
                "tr[itemtype], [class*='search-result']"
            )

            for card in cards[:50]:
                event = self._parse_card(card, source)
                if event:
                    events.append(event)
        except Exception as exc:
            logger.debug("WebSearch page scrape failed for %s: %s", source["url"], exc)
        finally:
            page.context.close()

        return events

    def _parse_card(self, card, source: dict) -> Optional[EventCreate]:
        try:
            name_el = card.query_selector("h2, h3, h4, [class*='title'], [class*='name']")
            name = name_el.inner_text().strip() if name_el else ""
            if not name or len(name) < 3:
                return None

            desc_el = card.query_selector("p, [class*='desc'], [class*='summary']")
            description = desc_el.inner_text().strip()[:500] if desc_el else ""

            date_el = card.query_selector("[class*='date'], time, [class*='when']")
            date_text = date_el.inner_text().strip() if date_el else ""
            start_date, end_date = self._parse_dates(date_text)

            loc_el = card.query_selector("[class*='location'], [class*='venue'], [class*='where']")
            location_text = loc_el.inner_text().strip() if loc_el else ""
            city, country = self._parse_location(location_text)

            link_el = card.query_selector("a[href]")
            url = ""
            if link_el:
                url = link_el.get_attribute("href") or ""
                if url and not url.startswith("http"):
                    url = ""

            return EventCreate(
                name=name,
                organizer=self._extract_organizer(description),
                category=self._infer_category(name, description),
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=url,
                brief_description=description,
                start_date=start_date,
                end_date=end_date or start_date,
                location=LocationModel(
                    city=city,
                    country=country,
                    continent=CONTINENT_MAP.get(country.lower(), ""),
                ),
                companies=[],
                source_url=source["url"],
                source_name=source["name"],
                source_confidence=0.50,
            )
        except Exception as exc:
            logger.debug("Failed to parse web search card: %s", exc)
            return None

    def _parse_dates(self, text: str) -> tuple[str, str]:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if len(dates) >= 2:
            return dates[0], dates[1]
        if len(dates) == 1:
            return dates[0], dates[0]
        return "", ""

    def _parse_location(self, text: str) -> tuple[str, str]:
        if not text:
            return "", ""
        parts = [p.strip() for p in text.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return text.strip(), ""

    def _infer_category(self, name: str, description: str) -> EventCategory:
        text = (name + " " + description).lower()
        if any(kw in text for kw in ["bank", "financ", "fintech", "payment"]):
            return EventCategory.BANKING_FINANCIAL
        if any(kw in text for kw in ["agri", "farm", "agriculture"]):
            return EventCategory.AGRIBUSINESS
        if any(kw in text for kw in ["health", "medical", "pharma"]):
            return EventCategory.MEDICAL
        if any(kw in text for kw in ["business", "entrepreneur", "startup"]):
            return EventCategory.BUSINESS
        return EventCategory.TECHNOLOGY

    def _extract_organizer(self, description: str) -> str:
        patterns = re.findall(
            r"(?:by|organized by|hosted by)\s+([A-Z][\w\s]+)", description, re.IGNORECASE
        )
        if patterns:
            return patterns[0].strip()[:100]
        return "Unknown"

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None
```

- [ ] **Step 2: Verify import**

```bash
cd /home/robson/code/hackaton/eventnexus && venv/bin/python -c "
from app.sources.web_search_source import WebSearchSource, SEARCH_URLS
print(f'OK: {len(SEARCH_URLS)} URLs, source={WebSearchSource().name}')
"
```
Expected: `OK: 107 URLs, source=web_search`

- [ ] **Step 3: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/web_search_source.py
git commit -m "fix(crawler): 10times/web search — rewrite with Playwright to bypass Cloudflare 403"
git push origin main
```

---

## Summary

| Task | Source | Problem | Fix |
|------|--------|---------|-----|
| 1 | Infrastructure | No browser engine | Add Playwright + shared browser pool |
| 2 | Ticketmaster | Most countries return 0 | Focus on 7 countries with coverage, 15 keywords |
| 3 | Eventbrite | API deprecated (404) | Playwright scraper of search pages |
| 4 | Sympla | React SPA (0 cards in static HTML) | Playwright with JS rendering |
| 5 | 10times | Cloudflare 403 | Playwright with real Chromium |
