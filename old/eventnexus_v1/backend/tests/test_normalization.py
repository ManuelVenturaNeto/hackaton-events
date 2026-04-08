"""Tests for normalization logic."""

from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.services.normalization_service import NormalizationService


class TestNormalization:
    """Tests for the NormalizationService."""

    def setup_method(self):
        """Set up normalizer for each test."""
        self.normalizer = NormalizationService()

    def test_country_normalization(self):
        """Should standardize country names."""
        event = EventCreate(
            name="Test",
            organizer="Org",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            location=LocationModel(country="united states"),
            source_name="test",
        )
        normalized = self.normalizer.normalize(event)
        assert normalized.location.country == "USA"

    def test_brazil_alias(self):
        """Should normalize 'brasil' to 'Brazil'."""
        event = EventCreate(
            name="Test",
            organizer="Org",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            location=LocationModel(country="brasil"),
            source_name="test",
        )
        normalized = self.normalizer.normalize(event)
        assert normalized.location.country == "Brazil"

    def test_continent_inference(self):
        """Should infer continent from country."""
        event = EventCreate(
            name="Test",
            organizer="Org",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            location=LocationModel(country="Brazil"),
            source_name="test",
        )
        normalized = self.normalizer.normalize(event)
        assert normalized.location.continent == "South America"

    def test_duration_calculation(self):
        """Should calculate duration from dates."""
        event = EventCreate(
            name="Test",
            organizer="Org",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            start_date="2025-09-01",
            end_date="2025-09-03",
            duration_days=0,
            location=LocationModel(country="USA"),
            source_name="test",
        )
        normalized = self.normalizer.normalize(event)
        assert normalized.duration_days == 3

    def test_whitespace_trimming(self):
        """Should trim whitespace from fields."""
        event = EventCreate(
            name="  Test Event  ",
            organizer="  Org  ",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            brief_description="  A description  ",
            official_website_url="  https://example.com/  ",
            location=LocationModel(country="USA"),
            source_name="test",
        )
        normalized = self.normalizer.normalize(event)
        assert normalized.name == "Test Event"
        assert normalized.organizer == "Org"
        assert normalized.brief_description == "A description"
        assert normalized.official_website_url == "https://example.com"
