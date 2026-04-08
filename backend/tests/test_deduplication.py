"""Tests for deduplication logic."""

from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)


class TestDeduplication:
    """Tests for event deduplication via the repository."""

    def test_same_event_different_sources(self, event_repo):
        """Same event from two sources should result in one record."""
        event1 = EventCreate(
            name="Tech Summit 2025",
            organizer="Org A",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            expected_audience_size=5000,
            official_website_url="https://example.com/summit",
            brief_description="First source description.",
            start_date="2027-08-01",
            end_date="2027-08-03",
            duration_days=3,
            location=LocationModel(city="New York", country="USA"),
            companies=[],
            source_name="source_a",
            source_url="https://source-a.com",
        )
        event2 = EventCreate(
            name="Tech Summit 2025",
            organizer="Org A",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            expected_audience_size=6000,
            official_website_url="https://example.com/summit",
            brief_description="Second source description, more details.",
            start_date="2027-08-01",
            end_date="2027-08-03",
            duration_days=3,
            location=LocationModel(city="New York", country="USA"),
            companies=[CompanyModel(name="BigCo", role=CompanyRole.SPONSOR)],
            source_name="source_b",
            source_url="https://source-b.com",
        )
        id1, new1 = event_repo.upsert_event(event1)
        id2, new2 = event_repo.upsert_event(event2)
        assert new1 is True
        assert new2 is False
        assert id1 == id2
        assert event_repo.get_event_count() == 1

    def test_different_events_not_deduped(self, event_repo):
        """Different events should not be deduplicated."""
        event1 = EventCreate(
            name="Event Alpha",
            organizer="Org A",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            start_date="2027-08-01",
            end_date="2025-08-02",
            duration_days=2,
            location=LocationModel(city="New York", country="USA"),
            source_name="test",
        )
        event2 = EventCreate(
            name="Event Beta",
            organizer="Org B",
            category=EventCategory.BUSINESS,
            format=EventFormat.ONLINE,
            status=EventStatus.UPCOMING,
            start_date="2027-09-01",
            end_date="2027-09-02",
            duration_days=2,
            location=LocationModel(city="London", country="UK"),
            source_name="test",
        )
        event_repo.upsert_event(event1)
        event_repo.upsert_event(event2)
        assert event_repo.get_event_count() == 2

    def test_dedup_key_case_insensitive(self, event_repo):
        """Dedup should be case insensitive."""
        event1 = EventCreate(
            name="MY EVENT",
            organizer="ORG",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            start_date="2027-06-01",
            end_date="2027-06-02",
            duration_days=2,
            location=LocationModel(city="Berlin", country="Germany"),
            source_name="test",
        )
        event2 = EventCreate(
            name="my event",
            organizer="org",
            category=EventCategory.TECHNOLOGY,
            format=EventFormat.IN_PERSON,
            status=EventStatus.UPCOMING,
            start_date="2027-06-01",
            end_date="2027-06-02",
            duration_days=2,
            location=LocationModel(city="berlin", country="germany"),
            source_name="test",
        )
        event_repo.upsert_event(event1)
        event_repo.upsert_event(event2)
        assert event_repo.get_event_count() == 1
