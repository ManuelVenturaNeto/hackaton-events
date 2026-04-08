"""Tests for API routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import database as db_module
from app.routes import health as health_mod
from app.routes import events as events_mod


@pytest.fixture
def client(test_db):
    """Patch the global db to use test database."""
    original = db_module.db
    db_module.db = test_db
    health_mod.db = test_db
    events_mod.db = test_db

    with TestClient(app) as c:
        yield c

    db_module.db = original
    health_mod.db = original
    events_mod.db = original


class TestHealthRoute:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data


class TestEventsRoutes:
    def test_list_events_empty(self, client):
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_events_with_data(self, client, sample_event):
        from app.repositories.event_repository import EventRepository
        repo = EventRepository(events_mod.db)
        repo.upsert_event(sample_event)

        resp = client.get("/api/events")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) == 1
        assert events[0]["name"] == "Test Tech Conference 2026"
        assert "location" in events[0]
        assert "companiesInvolved" in events[0]
        assert "sources" in events[0]

    def test_get_event_by_id(self, client, sample_event):
        from app.repositories.event_repository import EventRepository
        repo = EventRepository(events_mod.db)
        event_id, _ = repo.upsert_event(sample_event)

        resp = client.get(f"/api/events/{event_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == event_id

    def test_get_event_not_found(self, client):
        resp = client.get("/api/events/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_sync_returns_started(self, client):
        resp = client.post("/api/events/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sync_started"
        assert "runId" in data
