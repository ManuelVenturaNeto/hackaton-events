"""Tests for scoring logic."""

from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.services.scoring_service import ScoringService


class TestScoring:
    """Tests for the ScoringService."""

    def setup_method(self):
        """Set up scorer for each test."""
        self.scorer = ScoringService()

    def _make_event(self, **kwargs) -> EventCreate:
        """Create a minimal event with overrides."""
        defaults = {
            "name": "Test",
            "organizer": "Org",
            "category": EventCategory.TECHNOLOGY,
            "format": EventFormat.IN_PERSON,
            "status": EventStatus.UPCOMING,
            "expected_audience_size": 1000,
            "duration_days": 2,
            "location": LocationModel(country="USA"),
            "companies": [],
            "source_name": "test",
        }
        defaults.update(kwargs)
        return EventCreate(**defaults)

    def test_score_is_bounded(self):
        """Score should be between 0 and 100."""
        event = self._make_event()
        score = self.scorer.calculate_score(event)
        assert 0 <= score <= 100

    def test_larger_audience_scores_higher(self):
        """Events with larger audience should score higher."""
        small = self._make_event(expected_audience_size=100)
        large = self._make_event(expected_audience_size=50000)
        assert self.scorer.calculate_score(large) > self.scorer.calculate_score(small)

    def test_more_companies_scores_higher(self):
        """Events with more companies should score higher."""
        few = self._make_event(companies=[])
        many = self._make_event(companies=[
            CompanyModel(name=f"Co{i}", role=CompanyRole.SPONSOR) for i in range(10)
        ])
        assert self.scorer.calculate_score(many) > self.scorer.calculate_score(few)

    def test_brazil_bonus(self):
        """Brazil events should get a bonus."""
        us = self._make_event(location=LocationModel(country="USA"))
        br = self._make_event(location=LocationModel(country="Brazil"))
        assert self.scorer.calculate_score(br) > self.scorer.calculate_score(us)

    def test_in_person_scores_higher_than_online(self):
        """In-person events should score higher than online."""
        online = self._make_event(format=EventFormat.ONLINE)
        in_person = self._make_event(format=EventFormat.IN_PERSON)
        assert self.scorer.calculate_score(in_person) > self.scorer.calculate_score(online)

    def test_longer_duration_scores_higher(self):
        """Longer events should score higher."""
        short = self._make_event(duration_days=1)
        long = self._make_event(duration_days=5)
        assert self.scorer.calculate_score(long) > self.scorer.calculate_score(short)
