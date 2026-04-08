"""Eventbrite source adapter — Playwright + BeautifulSoup scraper."""

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
    """Scrapes events from Eventbrite search pages via Playwright + BS4."""

    @property
    def name(self) -> str:
        return "eventbrite"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for loc_slug, country_name in LOCATIONS:
            for keyword in SEARCH_KEYWORDS:
                try:
                    url = f"https://www.eventbrite.com/d/{loc_slug}/{keyword}/"
                    html = scrape_page(url)
                    events = self._parse_html(html, url, country_name)
                    all_events.extend(events)
                    if events:
                        logger.info("Eventbrite %s/%s: %d events", loc_slug, keyword, len(events))
                except Exception as exc:
                    logger.warning("Eventbrite %s/%s failed: %s", loc_slug, keyword, exc)

        logger.info("Eventbrite: fetched %d events total", len(all_events))
        return all_events

    def _parse_html(self, html: str, source_url: str, default_country: str) -> list[EventCreate]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        cards = soup.select(
            "[class*='event-card'], [data-testid*='event'], "
            "[class*='DiscoverHorizontalEventCard'], [class*='search-event-card'], "
            "article, [class*='eds-event-card']"
        )

        for card in cards[:30]:
            event = self._parse_card(card, source_url, default_country)
            if event:
                events.append(event)

        return events

    def _parse_card(self, card, source_url: str, default_country: str) -> Optional[EventCreate]:
        try:
            name_el = card.select_one("h2, h3, [class*='title'], [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                return None

            date_el = card.select_one("[class*='date'], time, [class*='start-date']")
            date_text = date_el.get_text(strip=True) if date_el else ""
            start_date = self._extract_date(date_text)

            loc_el = card.select_one("[class*='location'], [class*='venue'], [class*='card-text--truncated']")
            location_text = loc_el.get_text(strip=True) if loc_el else ""
            city = location_text.split(",")[0].strip() if location_text else ""

            link_el = card.select_one("a[href*='eventbrite.com/e/']")
            link = link_el.get("href", "") if link_el else ""
            if not link:
                link_el = card.select_one("a[href]")
                link = link_el.get("href", "") if link_el else ""

            desc_el = card.select_one("[class*='desc'], [class*='summary'], p")
            description = desc_el.get_text(strip=True)[:500] if desc_el else ""

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
                location=LocationModel(city=city, country=default_country),
                companies=[],
                source_url=source_url,
                source_name="eventbrite",
                source_confidence=0.70,
            )
        except Exception:
            return None

    def _extract_date(self, text: str) -> str:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        return dates[0] if dates else ""

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
