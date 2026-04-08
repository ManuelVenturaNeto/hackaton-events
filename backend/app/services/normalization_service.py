"""Service for normalizing event data before persistence.

Normalization includes:
- Trimming whitespace
- Standardizing country names
- Calculating duration from dates
- Ensuring required fields have defaults
- Cleaning URLs
"""

import logging
from datetime import datetime

from app.models.event import EventCreate

logger = logging.getLogger(__name__)

# Country name standardization map
COUNTRY_ALIASES = {
    "united states": "USA",
    "united states of america": "USA",
    "us": "USA",
    "u.s.a.": "USA",
    "united kingdom": "UK",
    "great britain": "UK",
    "england": "UK",
    "brasil": "Brazil",
    "deutschland": "Germany",
    "españa": "Spain",
    "emirates": "UAE",
    "united arab emirates": "UAE",
}

# Continent mapping for common countries
COUNTRY_TO_CONTINENT = {
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "North America",
    "Brazil": "South America",
    "Argentina": "South America",
    "Chile": "South America",
    "Colombia": "South America",
    "UK": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Spain": "Europe",
    "Portugal": "Europe",
    "Italy": "Europe",
    "Netherlands": "Europe",
    "Switzerland": "Europe",
    "China": "Asia",
    "Japan": "Asia",
    "India": "Asia",
    "Singapore": "Asia",
    "UAE": "Asia",
    "Israel": "Asia",
    "South Korea": "Asia",
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    "South Africa": "Africa",
    "Nigeria": "Africa",
}


class NormalizationService:
    """Normalizes raw event data into clean, consistent format.

    Handles country name standardization, date calculations,
    whitespace cleanup, and continent inference.
    """

    def normalize(self, event: EventCreate) -> EventCreate:
        """Normalize an event's data fields.

        Args:
            event: Raw event data.

        Returns:
            Normalized EventCreate with cleaned fields.
        """
        event.name = event.name.strip()
        event.organizer = event.organizer.strip()
        event.brief_description = event.brief_description.strip()
        event.official_website_url = event.official_website_url.strip().rstrip("/")

        # Normalize country
        country_lower = event.location.country.strip().lower()
        if country_lower in COUNTRY_ALIASES:
            event.location.country = COUNTRY_ALIASES[country_lower]

        # Infer continent if missing
        if not event.location.continent:
            event.location.continent = COUNTRY_TO_CONTINENT.get(
                event.location.country, ""
            )

        # Calculate duration if dates present and duration is 0
        if event.start_date and event.end_date and event.duration_days == 0:
            event.duration_days = self._calc_duration(event.start_date, event.end_date)

        # Ensure duration is at least 1
        if event.duration_days < 1:
            event.duration_days = 1

        logger.debug("Normalized event: %s", event.name)
        return event

    def _calc_duration(self, start: str, end: str) -> int:
        """Calculate duration in days between ISO date strings.

        Args:
            start: Start date string.
            end: End date string.

        Returns:
            Number of days, minimum 1.
        """
        try:
            s = datetime.fromisoformat(start)
            e = datetime.fromisoformat(end)
            return max(1, (e - s).days + 1)
        except (ValueError, TypeError):
            return 1
