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
