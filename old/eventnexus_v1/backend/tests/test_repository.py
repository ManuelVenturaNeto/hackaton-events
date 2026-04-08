"""Tests for event repository operations."""


class TestEventRepository:
    """Tests for EventRepository CRUD operations."""

    def test_insert_event(self, event_repo, sample_event):
        """New events should be inserted successfully."""
        event_id, was_new = event_repo.upsert_event(sample_event)
        assert was_new is True
        assert event_id is not None

    def test_duplicate_insert_updates(self, event_repo, sample_event):
        """Inserting the same event twice should update, not duplicate."""
        event_id_1, was_new_1 = event_repo.upsert_event(sample_event)
        event_id_2, was_new_2 = event_repo.upsert_event(sample_event)
        assert was_new_1 is True
        assert was_new_2 is False
        assert event_id_1 == event_id_2

    def test_get_event_by_id(self, event_repo, sample_event):
        """Should retrieve event by ID with all related data."""
        event_id, _ = event_repo.upsert_event(sample_event)
        event = event_repo.get_event_by_id(event_id)
        assert event is not None
        assert event.name == "Test Tech Conference 2025"
        assert event.location["city"] == "Test City"
        assert len(event.companiesInvolved) == 2

    def test_get_event_not_found(self, event_repo):
        """Should return None for nonexistent ID."""
        assert event_repo.get_event_by_id("nonexistent") is None

    def test_list_events_no_filter(self, event_repo, sample_event):
        """Should list all events without filters."""
        event_repo.upsert_event(sample_event)
        events = event_repo.list_events()
        assert len(events) == 1

    def test_list_events_filter_category(self, event_repo, sample_event, sample_brazil_event):
        """Should filter events by category."""
        event_repo.upsert_event(sample_event)
        event_repo.upsert_event(sample_brazil_event)
        events = event_repo.list_events(category="Technology")
        assert len(events) == 2

    def test_list_events_filter_country(self, event_repo, sample_event, sample_brazil_event):
        """Should filter events by country."""
        event_repo.upsert_event(sample_event)
        event_repo.upsert_event(sample_brazil_event)
        events = event_repo.list_events(country="Brazil")
        assert len(events) == 1
        assert events[0].location["country"] == "Brazil"

    def test_list_events_filter_status(self, event_repo, sample_event):
        """Should filter events by status."""
        event_repo.upsert_event(sample_event)
        events = event_repo.list_events(status="upcoming")
        assert len(events) == 1
        events = event_repo.list_events(status="canceled")
        assert len(events) == 0

    def test_list_events_search(self, event_repo, sample_event):
        """Should search by name, organizer, description."""
        event_repo.upsert_event(sample_event)
        events = event_repo.list_events(search="Test Tech")
        assert len(events) == 1
        events = event_repo.list_events(search="nonexistent keyword")
        assert len(events) == 0

    def test_list_events_sort(self, event_repo, sample_event, sample_brazil_event):
        """Should sort events by specified field."""
        event_repo.upsert_event(sample_event)
        event_repo.upsert_event(sample_brazil_event)
        events = event_repo.list_events(sort_by="audienceSize", sort_order="desc")
        assert events[0].expectedAudienceSize >= events[1].expectedAudienceSize

    def test_update_status(self, event_repo, sample_event):
        """Should update event status."""
        event_id, _ = event_repo.upsert_event(sample_event)
        result = event_repo.update_status(event_id, "canceled")
        assert result is True
        event = event_repo.get_event_by_id(event_id)
        assert event.status == "canceled"

    def test_get_event_count(self, event_repo, sample_event, sample_brazil_event):
        """Should count events correctly."""
        assert event_repo.get_event_count() == 0
        event_repo.upsert_event(sample_event)
        assert event_repo.get_event_count() == 1
        event_repo.upsert_event(sample_brazil_event)
        assert event_repo.get_event_count() == 2

    def test_list_events_filter_company(self, event_repo, sample_event):
        """Should filter events by company name."""
        event_repo.upsert_event(sample_event)
        events = event_repo.list_events(company="Sponsor Inc")
        assert len(events) == 1
        events = event_repo.list_events(company="Nonexistent Corp")
        assert len(events) == 0

    def test_list_events_date_range(self, event_repo, sample_event):
        """Should filter events by date range."""
        event_repo.upsert_event(sample_event)
        events = event_repo.list_events(start_date_from="2025-01-01", start_date_to="2025-12-31")
        assert len(events) == 1
        events = event_repo.list_events(start_date_from="2026-01-01")
        assert len(events) == 0
