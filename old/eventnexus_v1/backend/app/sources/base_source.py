"""Base class for event source adapters."""

import logging
from abc import ABC, abstractmethod

from app.models.event import EventCreate

logger = logging.getLogger(__name__)


class BaseEventSource(ABC):
    """Abstract base class for all event source adapters.

    Each source adapter is responsible for fetching event data from
    a specific type of source (web scraping, API, curated list, etc.)
    and returning normalized EventCreate objects.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable source name."""

    @abstractmethod
    def fetch_events(self) -> list[EventCreate]:
        """Fetch events from this source.

        Returns:
            List of EventCreate models ready for persistence.
        """

    @abstractmethod
    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        """Check if an event's status has changed.

        Args:
            event_name: The event name.
            event_url: The official website URL.

        Returns:
            New status string if changed, or None if unchanged/unknown.
        """
