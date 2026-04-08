"""Tests for event and sync_run repositories."""

import pytest

from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository


class TestEventRepository:
    def test_upsert_inserts_new_event(self, test_db, sample_event):
        repo = EventRepository(test_db)
        event_id, was_new = repo.upsert_event(sample_event)
        assert was_new is True
        assert event_id is not None

    def test_upsert_updates_existing_event(self, test_db, sample_event):
        repo = EventRepository(test_db)
        id1, new1 = repo.upsert_event(sample_event)
        sample_event.expected_audience_size = 9999
        id2, new2 = repo.upsert_event(sample_event)
        assert id1 == id2
        assert new2 is False

    def test_get_event_by_id(self, test_db, sample_event):
        repo = EventRepository(test_db)
        event_id, _ = repo.upsert_event(sample_event)
        result = repo.get_event_by_id(event_id)
        assert result is not None
        assert result.name == "Test Tech Conference 2026"
        assert result.location.city == "Test City"
        assert len(result.companiesInvolved) == 2

    def test_get_event_by_id_not_found(self, test_db):
        repo = EventRepository(test_db)
        result = repo.get_event_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_list_events_default_upcoming(self, test_db, sample_event):
        repo = EventRepository(test_db)
        repo.upsert_event(sample_event)
        events = repo.list_events()
        assert len(events) == 1
        assert events[0].status == "upcoming"

    def test_list_events_filter_by_country(self, test_db, sample_event, sample_brazil_event):
        repo = EventRepository(test_db)
        repo.upsert_event(sample_event)
        repo.upsert_event(sample_brazil_event)
        events = repo.list_events(country="Brazil")
        assert len(events) == 1
        assert events[0].location.country == "Brazil"

    def test_list_events_search(self, test_db, sample_event, sample_brazil_event):
        repo = EventRepository(test_db)
        repo.upsert_event(sample_event)
        repo.upsert_event(sample_brazil_event)
        events = repo.list_events(search="brasil")
        assert len(events) == 1

    def test_list_events_sort_by_score(self, test_db, sample_event, sample_brazil_event):
        repo = EventRepository(test_db)
        sample_event.networking_relevance_score = 50
        sample_brazil_event.networking_relevance_score = 90
        repo.upsert_event(sample_event)
        repo.upsert_event(sample_brazil_event)
        events = repo.list_events(sort_by="networkingRelevance", sort_order="desc")
        assert events[0].networkingRelevanceScore >= events[1].networkingRelevanceScore


class TestSyncRunRepository:
    def test_start_and_complete_run(self, test_db):
        repo = SyncRunRepository(test_db)
        run_id = repo.start_run("populate")
        assert run_id is not None
        repo.complete_run(run_id, status="completed", events_discovered=10, events_inserted=8)
        runs = repo.get_recent_runs(limit=1)
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
        assert runs[0]["events_discovered"] == 10
