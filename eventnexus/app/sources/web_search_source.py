"""Web search source adapter for discovering events from public web sources.

Discovery strategy:
- Searches known public event listing sites and aggregators
- Uses HTTP GET requests to fetch event listing pages
- Parses structured data from HTML when available
- Falls back to text extraction for unstructured pages
- Prioritizes official event websites
- Handles network errors gracefully

Searched source types:
- Event aggregator sites (10times.com, eventbrite.com, etc.)
- Official conference websites
- Industry association calendars
- Tech community event listings

Concurrency:
- Uses ThreadPoolExecutor for parallel HTTP fetches
- Controlled by max_concurrent_fetches setting
- Each source URL is fetched independently
- Results are merged after all fetches complete
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)

logger = logging.getLogger(__name__)

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


class WebSearchSource:
    """Source adapter that discovers events by scraping public event listing sites.

    Uses concurrent HTTP requests to fetch multiple sources in parallel,
    then parses and normalizes the discovered event data.

    Search strategy:
    - Global: Searches international event aggregators for tech conferences,
      trade shows, and industry events
    - Brazil: Searches Brazil-specific event listings across all supported
      categories (tech, finance, agri, medical, business)
    - Deduplication happens downstream in the repository layer

    Concurrency approach:
    - ThreadPoolExecutor with configurable max_workers
    - Each URL fetch is an independent task
    - Network timeouts prevent hanging on slow sources
    - Failed fetches are logged but don't block other sources
    """

    def __init__(self) -> None:
        """Initialize the web search source."""
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": "NetworkX-EventDiscovery/1.0 (Research Bot)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    @property
    def name(self) -> str:
        """Return the source name."""
        return "web_search"

    def fetch_events(self) -> list[EventCreate]:
        """Fetch events from all configured web sources concurrently.

        Uses ThreadPoolExecutor to parallelize HTTP requests across
        all configured source URLs.

        Returns:
            List of EventCreate objects discovered from web sources.
        """
        all_events: list[EventCreate] = []
        errors: list[str] = []

        with ThreadPoolExecutor(max_workers=settings.max_concurrent_fetches) as executor:
            future_to_source = {
                executor.submit(self._fetch_single_source, source): source
                for source in SEARCH_URLS
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    events = future.result()
                    all_events.extend(events)
                    logger.info("Source %s yielded %d events", source["name"], len(events))
                except Exception as exc:
                    error_msg = f"Source {source['name']} failed: {exc}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

        logger.info("Web search discovered %d total events with %d errors",
                     len(all_events), len(errors))
        return all_events

    def _fetch_single_source(self, source: dict) -> list[EventCreate]:
        """Fetch and parse events from a single source URL.

        Args:
            source: Dict with 'url', 'name', and 'region' keys.

        Returns:
            List of parsed EventCreate objects.
        """
        try:
            response = self._client.get(source["url"])
            response.raise_for_status()
            return self._parse_html_events(response.text, source)
        except httpx.HTTPError as exc:
            logger.warning("HTTP error fetching %s: %s", source["url"], exc)
            return []
        except Exception as exc:
            logger.warning("Error processing %s: %s", source["url"], exc)
            return []

    def _parse_html_events(self, html: str, source: dict) -> list[EventCreate]:
        """Parse event data from HTML content.

        Attempts to extract structured event information from common
        HTML patterns used by event listing sites.

        Args:
            html: Raw HTML content.
            source: Source metadata dict.

        Returns:
            List of parsed EventCreate objects.
        """
        soup = BeautifulSoup(html, "lxml")
        events: list[EventCreate] = []

        # Try to find event cards/listings in common HTML structures
        event_elements = soup.select(
            "[class*='event-card'], [class*='event-item'], "
            "[class*='EventCard'], [class*='listing-item'], "
            "[data-type='event'], .event, .conference-item"
        )

        for elem in event_elements[:50]:  # Limit to prevent overscraping
            event = self._extract_event_from_element(elem, source)
            if event:
                events.append(event)

        return events

    def _extract_event_from_element(self, elem, source: dict) -> Optional[EventCreate]:
        """Extract event data from an HTML element.

        Args:
            elem: BeautifulSoup element containing event data.
            source: Source metadata dict.

        Returns:
            EventCreate if successfully parsed, None otherwise.
        """
        try:
            name = self._extract_text(elem, "h2, h3, h4, [class*='title'], [class*='name']")
            if not name or len(name) < 3:
                return None

            description = self._extract_text(elem, "p, [class*='desc'], [class*='summary']")
            date_text = self._extract_text(elem, "[class*='date'], time, [class*='when']")
            location_text = self._extract_text(elem, "[class*='location'], [class*='venue'], [class*='where']")

            link = elem.select_one("a[href]")
            url = link.get("href", "") if link else ""
            if url and not url.startswith("http"):
                url = ""

            city, country = self._parse_location_text(location_text or "")
            start_date, end_date = self._parse_date_text(date_text or "")
            category = self._infer_category(name, description or "")

            return EventCreate(
                name=name.strip(),
                organizer=self._extract_organizer(name, description or ""),
                category=category,
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=url,
                brief_description=(description or "").strip()[:500],
                start_date=start_date,
                end_date=end_date or start_date,
                duration_days=max(1, self._calc_duration(start_date, end_date)),
                location=LocationModel(
                    city=city,
                    country=country,
                    continent=self._infer_continent(country),
                ),
                companies=[],
                source_url=source["url"],
                source_name=source["name"],
                source_confidence=0.5,
            )
        except Exception as exc:
            logger.debug("Failed to extract event from element: %s", exc)
            return None

    def _extract_text(self, parent, selector: str) -> str:
        """Safely extract text from an element matching a CSS selector.

        Args:
            parent: Parent BeautifulSoup element.
            selector: CSS selector string.

        Returns:
            Extracted text or empty string.
        """
        elem = parent.select_one(selector)
        return elem.get_text(strip=True) if elem else ""

    def _parse_location_text(self, text: str) -> tuple[str, str]:
        """Parse city and country from location text.

        Args:
            text: Raw location text.

        Returns:
            Tuple of (city, country).
        """
        if not text:
            return "", ""
        parts = [p.strip() for p in text.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return text.strip(), ""

    def _parse_date_text(self, text: str) -> tuple[str, str]:
        """Parse start and end dates from date text.

        Args:
            text: Raw date text.

        Returns:
            Tuple of (start_date, end_date) in ISO format.
        """
        if not text:
            return "", ""
        date_pattern = r"\d{4}-\d{2}-\d{2}"
        dates = re.findall(date_pattern, text)
        if len(dates) >= 2:
            return dates[0], dates[1]
        if len(dates) == 1:
            return dates[0], dates[0]
        return "", ""

    def _calc_duration(self, start: str, end: str) -> int:
        """Calculate duration in days between two date strings.

        Args:
            start: Start date in ISO format.
            end: End date in ISO format.

        Returns:
            Duration in days, minimum 1.
        """
        try:
            if start and end:
                s = datetime.fromisoformat(start)
                e = datetime.fromisoformat(end)
                return max(1, (e - s).days + 1)
        except ValueError:
            pass
        return 1

    def _infer_category(self, name: str, description: str) -> EventCategory:
        """Infer event category from name and description.

        Args:
            name: Event name.
            description: Event description.

        Returns:
            Best-matching EventCategory.
        """
        text = (name + " " + description).lower()
        if any(kw in text for kw in ["bank", "financ", "fintech", "payment", "money"]):
            return EventCategory.BANKING_FINANCIAL
        if any(kw in text for kw in ["agri", "farm", "crop", "agriculture"]):
            return EventCategory.AGRIBUSINESS
        if any(kw in text for kw in ["health", "medical", "pharma", "hospital", "clinic"]):
            return EventCategory.MEDICAL
        if any(kw in text for kw in ["business", "entrepreneur", "startup", "retail", "commerce"]):
            return EventCategory.BUSINESS
        return EventCategory.TECHNOLOGY

    def _extract_organizer(self, name: str, description: str) -> str:
        """Extract or infer organizer from event information.

        Args:
            name: Event name.
            description: Event description.

        Returns:
            Organizer name or 'Unknown'.
        """
        by_patterns = re.findall(r"(?:by|organized by|hosted by)\s+([A-Z][\w\s]+)", description, re.IGNORECASE)
        if by_patterns:
            return by_patterns[0].strip()[:100]
        return "Unknown"

    def _infer_continent(self, country: str) -> str:
        """Infer continent from country name.

        Args:
            country: Country name.

        Returns:
            Continent name or empty string.
        """
        country_lower = country.lower()
        continent_map = {
            "usa": "North America", "united states": "North America", "canada": "North America",
            "mexico": "North America",
            "brazil": "South America", "argentina": "South America", "chile": "South America",
            "colombia": "South America",
            "uk": "Europe", "germany": "Europe", "france": "Europe", "spain": "Europe",
            "portugal": "Europe", "italy": "Europe", "netherlands": "Europe",
            "china": "Asia", "japan": "Asia", "india": "Asia", "singapore": "Asia",
            "uae": "Asia", "israel": "Asia", "south korea": "Asia",
            "australia": "Oceania", "new zealand": "Oceania",
            "south africa": "Africa", "nigeria": "Africa", "kenya": "Africa",
        }
        return continent_map.get(country_lower, "")

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        """Check if an event page indicates a status change.

        Fetches the event's official page and looks for cancellation
        or postponement indicators in the page content.

        Args:
            event_name: The event name.
            event_url: The official website URL.

        Returns:
            New status string if a change is detected, None otherwise.
        """
        if not event_url:
            return None
        try:
            response = self._client.get(event_url)
            response.raise_for_status()
            text = response.text.lower()

            if any(kw in text for kw in ["cancel", "cancelled", "canceled"]):
                logger.info("Detected cancellation signal for %s", event_name)
                return "canceled"
            if any(kw in text for kw in ["postpone", "postponed", "reschedul"]):
                logger.info("Detected postponement signal for %s", event_name)
                return "postponed"
        except Exception as exc:
            logger.debug("Could not check status for %s: %s", event_name, exc)

        return None

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
