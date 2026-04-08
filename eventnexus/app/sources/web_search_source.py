"""Web search source — Playwright + BeautifulSoup scraper.

Uses Playwright to bypass Cloudflare on 10times.com, then BeautifulSoup to parse.
Deep search: 21 countries x 5 categories + confs.tech.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource
from app.sources.browser_pool import scrape_page

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
    # URLs adicionais em português para cobertura brasileira
    for category in _CATEGORIES_10TIMES:
        urls.append({
            "url": f"https://10times.com/brazil/{category}?lang=pt",
            "name": f"10times_brazil_{category}_pt",
            "region": "brazil",
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
    "uae": "Asia",
    "australia": "Oceania", "new zealand": "Oceania",
}


class WebSearchSource(BaseEventSource):
    """Scrapes event sites via Playwright (render) + BeautifulSoup (parse)."""

    @property
    def name(self) -> str:
        return "web_search"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for source in SEARCH_URLS:
            try:
                html = scrape_page(source["url"])
                events = self._parse_html(html, source)
                if events:
                    all_events.extend(events)
                    logger.info("WebSearch %s: %d events", source["name"], len(events))
            except Exception as exc:
                logger.warning("WebSearch %s failed: %s", source["name"], exc)

        logger.info("WebSearch: fetched %d events from %d URLs", len(all_events), len(SEARCH_URLS))
        return all_events

    def _parse_html(self, html: str, source: dict) -> list[EventCreate]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        cards = soup.select(
            "[class*='event-card'], [class*='event-item'], "
            "[class*='EventCard'], [class*='listing-item'], "
            "[data-type='event'], .event, .conference-item, "
            "tr[itemtype], [class*='search-result']"
        )

        for card in cards[:50]:
            event = self._parse_card(card, source)
            if event:
                events.append(event)

        return events

    def _parse_card(self, card, source: dict) -> Optional[EventCreate]:
        try:
            name_el = card.select_one("h2, h3, h4, [class*='title'], [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                return None

            desc_el = card.select_one("p, [class*='desc'], [class*='summary']")
            description = desc_el.get_text(strip=True)[:500] if desc_el else ""

            date_el = card.select_one("[class*='date'], time, [class*='when']")
            date_text = date_el.get_text(strip=True) if date_el else ""
            start_date, end_date = self._parse_dates(date_text)

            loc_el = card.select_one("[class*='location'], [class*='venue'], [class*='where']")
            location_text = loc_el.get_text(strip=True) if loc_el else ""
            city, country = self._parse_location(location_text)

            link_el = card.select_one("a[href]")
            url = link_el.get("href", "") if link_el else ""
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
        except Exception:
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
        return patterns[0].strip()[:100] if patterns else "Unknown"

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None
