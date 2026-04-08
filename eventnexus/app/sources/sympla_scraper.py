"""Sympla web scraper — Playwright + BeautifulSoup.

Sympla is a React SPA. Playwright renders JS, BeautifulSoup parses the HTML.
Deep search: all 27 Brazilian states x 5 categories.
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
    """Scrapes Sympla via Playwright (JS render) + BeautifulSoup (parse)."""

    @property
    def name(self) -> str:
        return "sympla"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for source in SYMPLA_URLS:
            try:
                html = scrape_page(source["url"])
                events = self._parse_html(html, source)
                if events:
                    all_events.extend(events)
                    logger.info("Sympla %s: %d events", source["name"], len(events))
            except Exception as exc:
                logger.warning("Sympla %s failed: %s", source["name"], exc)

        logger.info("Sympla: fetched %d events from %d URLs", len(all_events), len(SYMPLA_URLS))
        return all_events

    def _parse_html(self, html: str, source: dict) -> list[EventCreate]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        cards = soup.select(
            "[class*='event-card'], [class*='EventCard'], "
            "[class*='event-item'], a[href*='/evento/'], "
            "[class*='sympla-card'], [data-testid*='event']"
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
            city = location_text.split(",")[0].strip() if location_text else ""

            link = card.get("href", "")
            if not link:
                a = card.select_one("a[href]")
                link = a.get("href", "") if a else ""
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
        except Exception:
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
