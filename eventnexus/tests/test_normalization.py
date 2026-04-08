"""Tests for the normalization service."""

from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.services.normalization_service import NormalizationService


def _make_event(**overrides) -> EventCreate:
    defaults = dict(
        name="  Test Event  ",
        organizer="  Test Org  ",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        brief_description="  A description  ",
        official_website_url="https://example.com/event/",
        start_date="2026-09-15",
        end_date="2026-09-17",
        duration_days=0,
        location=LocationModel(country="brasil", city="São Paulo"),
    )
    defaults.update(overrides)
    return EventCreate(**defaults)


class TestNormalizationService:
    def setup_method(self):
        self.svc = NormalizationService()

    def test_trims_whitespace(self):
        event = self.svc.normalize(_make_event())
        assert event.name == "Test Event"
        assert event.organizer == "Test Org"
        assert event.brief_description == "A description"

    def test_strips_trailing_slash_from_url(self):
        event = self.svc.normalize(_make_event())
        assert event.official_website_url == "https://example.com/event"

    def test_normalizes_country_alias(self):
        event = self.svc.normalize(_make_event())
        assert event.location.country == "Brazil"

    def test_infers_continent(self):
        event = self.svc.normalize(_make_event())
        assert event.location.continent == "South America"

    def test_calculates_duration(self):
        event = self.svc.normalize(_make_event())
        assert event.duration_days == 3

    def test_duration_minimum_one(self):
        event = self.svc.normalize(_make_event(start_date="", end_date="", duration_days=0))
        assert event.duration_days == 1

    def test_preserves_existing_continent(self):
        event = self.svc.normalize(
            _make_event(location=LocationModel(country="Brazil", continent="Already Set"))
        )
        assert event.location.continent == "Already Set"
