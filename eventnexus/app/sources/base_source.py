"""Base class for event source adapters."""

from abc import ABC, abstractmethod

from app.models.event import EventCreate


class BaseEventSource(ABC):
    """Abstract base class for all event source adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable source name."""

    @abstractmethod
    def fetch_events(self) -> list[EventCreate]:
        """Fetch events from this source."""

    @abstractmethod
    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        """Check if an event's status has changed.

        Returns new status string if changed, or None.
        """
