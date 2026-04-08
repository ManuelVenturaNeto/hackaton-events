"""Tests for the scoring service."""

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


def _make_event(**overrides) -> EventCreate:
    defaults = dict(
        name="Test",
        organizer="Org",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        expected_audience_size=5000,
        duration_days=3,
        location=LocationModel(country="USA"),
        companies=[
            CompanyModel(name="A", role=CompanyRole.ORGANIZER),
            CompanyModel(name="B", role=CompanyRole.SPONSOR),
            CompanyModel(name="C", role=CompanyRole.EXHIBITOR),
        ],
    )
    defaults.update(overrides)
    return EventCreate(**defaults)


class TestScoringService:
    def setup_method(self):
        self.scorer = ScoringService()

    def test_score_within_range(self):
        score = self.scorer.calculate_score(_make_event())
        assert 0 <= score <= 100

    def test_audience_scoring(self):
        small = self.scorer.calculate_score(_make_event(expected_audience_size=500))
        large = self.scorer.calculate_score(_make_event(expected_audience_size=100000))
        assert large > small

    def test_brazil_bonus(self):
        usa = self.scorer.calculate_score(_make_event(location=LocationModel(country="USA")))
        brazil = self.scorer.calculate_score(_make_event(location=LocationModel(country="Brazil")))
        assert brazil - usa == 10

    def test_company_diversity(self):
        no_companies = self.scorer.calculate_score(_make_event(companies=[]))
        many = self.scorer.calculate_score(_make_event(companies=[
            CompanyModel(name=f"Co{i}", role=CompanyRole.SPONSOR) for i in range(10)
        ]))
        assert many > no_companies

    def test_format_scoring(self):
        online = self.scorer.calculate_score(_make_event(format=EventFormat.ONLINE))
        in_person = self.scorer.calculate_score(_make_event(format=EventFormat.IN_PERSON))
        assert in_person > online

    def test_score_capped_at_100(self):
        maxed = _make_event(
            expected_audience_size=200000,
            duration_days=5,
            location=LocationModel(country="Brazil"),
            companies=[CompanyModel(name=f"Co{i}", role=CompanyRole.SPONSOR) for i in range(15)],
        )
        score = self.scorer.calculate_score(maxed)
        assert score == 100
