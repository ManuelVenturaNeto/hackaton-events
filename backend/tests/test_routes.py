"""Tests for API routes."""

from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.repositories.event_repository import EventRepository


def _insert_test_event(tmp_db, name="Route Test Event", country="USA", category="Technology"):
    """Helper to insert a test event directly."""
    repo = EventRepository(tmp_db)
    event = EventCreate(
        name=name,
        organizer="Test Org",
        category=EventCategory(category),
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        expected_audience_size=5000,
        official_website_url="https://example.com/test",
        brief_description="Test event for route testing.",
        start_date="2027-09-15",
        end_date="2027-09-17",
        duration_days=3,
        location=LocationModel(city="Test City", country=country, continent="North America"),
        companies=[CompanyModel(name="TestCo", role=CompanyRole.ORGANIZER)],
        source_url="https://example.com",
        source_name="test",
        source_confidence=1.0,
        networking_relevance_score=75.0,
    )
    return repo.upsert_event(event)


class TestHealthRoute:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestListEventsRoute:
    """Tests for the GET /api/events endpoint."""

    def test_list_events_empty(self, client):
        """Should return empty list when no events exist."""
        response = client.get("/api/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_events_with_data(self, client, tmp_db):
        """Should return events after insertion."""
        _insert_test_event(tmp_db)
        response = client.get("/api/events")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["name"] == "Route Test Event"

    def test_list_events_filter_country(self, client, tmp_db):
        """Should filter by country query param."""
        _insert_test_event(tmp_db, name="US Event", country="USA")
        _insert_test_event(tmp_db, name="Brazil Event", country="Brazil")
        response = client.get("/api/events?country=Brazil")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["name"] == "Brazil Event"

    def test_list_events_filter_category(self, client, tmp_db):
        """Should filter by category query param."""
        _insert_test_event(tmp_db, name="Tech Event", category="Technology")
        _insert_test_event(tmp_db, name="Finance Event", category="Banking / Financial")
        response = client.get("/api/events?category=Technology")
        events = response.json()
        assert len(events) == 1
        assert events[0]["name"] == "Tech Event"

    def test_list_events_search(self, client, tmp_db):
        """Should filter by search query param."""
        _insert_test_event(tmp_db, name="AWS re:Invent Special")
        response = client.get("/api/events?search=AWS")
        events = response.json()
        assert len(events) == 1

    def test_list_events_response_shape(self, client, tmp_db):
        """Response should match the frontend Event interface."""
        _insert_test_event(tmp_db)
        response = client.get("/api/events")
        event = response.json()[0]
        required_fields = [
            "id", "name", "location", "startDate", "endDate",
            "durationDays", "organizer", "category", "format",
            "companiesInvolved", "expectedAudienceSize", "status",
            "officialWebsiteUrl", "briefDescription",
            "networkingRelevanceScore", "lastUpdated",
        ]
        for field in required_fields:
            assert field in event, f"Missing field: {field}"
        assert "venueName" in event["location"]
        assert "city" in event["location"]
        assert "country" in event["location"]


class TestGetEventRoute:
    """Tests for the GET /api/events/{event_id} endpoint."""

    def test_get_event_found(self, client, tmp_db):
        """Should return full event details for valid ID."""
        event_id, _ = _insert_test_event(tmp_db)
        response = client.get(f"/api/events/{event_id}")
        assert response.status_code == 200
        assert response.json()["id"] == event_id

    def test_get_event_not_found(self, client):
        """Should return 404 for nonexistent event."""
        response = client.get("/api/events/nonexistent-id")
        assert response.status_code == 404


class TestPopulateRoute:
    """Tests for the POST /api/events/populate endpoint."""

    def test_populate_creates_events(self, client):
        """Populate should discover and insert events."""
        response = client.post("/api/events/populate")
        assert response.status_code == 200
        data = response.json()
        assert data["events_discovered"] > 0
        assert data["events_inserted"] > 0

    def test_populate_idempotent(self, client):
        """Running populate twice should not create duplicates."""
        client.post("/api/events/populate")
        response1 = client.get("/api/events")
        count1 = len(response1.json())

        client.post("/api/events/populate")
        response2 = client.get("/api/events")
        count2 = len(response2.json())

        assert count1 == count2


class TestRefreshStatusRoute:
    """Tests for the POST /api/events/refresh-status endpoint."""

    def test_refresh_status(self, client, tmp_db):
        """Refresh-status should check events without errors."""
        _insert_test_event(tmp_db)
        response = client.post("/api/events/refresh-status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["events_checked"] >= 0


class TestSyncRoute:
    """Tests for the POST /api/events/sync endpoint."""

    def test_sync_runs_both(self, client):
        """Sync should run populate and refresh."""
        response = client.post("/api/events/sync")
        assert response.status_code == 200
        data = response.json()
        assert "populate" in data
        assert "refresh" in data
