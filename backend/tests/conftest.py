"""Shared test fixtures."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.main import app
from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository
from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)


@pytest.fixture
def tmp_db():
    """Create a temporary SQLite database for testing.

    Yields:
        Database instance pointing to a temp file.
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(db_path=path)
    database.initialize()
    yield database
    database.close()
    os.unlink(path)


@pytest.fixture
def event_repo(tmp_db):
    """Create an EventRepository with a temp database.

    Args:
        tmp_db: Temporary Database fixture.

    Yields:
        EventRepository instance.
    """
    return EventRepository(tmp_db)


@pytest.fixture
def sync_repo(tmp_db):
    """Create a SyncRunRepository with a temp database.

    Args:
        tmp_db: Temporary Database fixture.

    Yields:
        SyncRunRepository instance.
    """
    return SyncRunRepository(tmp_db)


@pytest.fixture
def sample_event() -> EventCreate:
    """Create a sample event for testing.

    Returns:
        EventCreate with realistic test data.
    """
    return EventCreate(
        name="Test Tech Conference 2025",
        organizer="Test Corp",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        expected_audience_size=5000,
        official_website_url="https://example.com/test-conf",
        brief_description="A test technology conference for unit testing.",
        start_date="2027-09-15",
        end_date="2027-09-17",
        duration_days=3,
        location=LocationModel(
            venue_name="Test Convention Center",
            full_street_address="123 Test St",
            city="Test City",
            state_province="Test State",
            country="USA",
            postal_code="12345",
            continent="North America",
        ),
        companies=[
            CompanyModel(name="Test Corp", role=CompanyRole.ORGANIZER),
            CompanyModel(name="Sponsor Inc", role=CompanyRole.SPONSOR),
        ],
        source_url="https://example.com/test-conf",
        source_name="test_source",
        source_confidence=0.9,
    )


@pytest.fixture
def sample_brazil_event() -> EventCreate:
    """Create a sample Brazil event for testing.

    Returns:
        EventCreate with Brazil-specific test data.
    """
    return EventCreate(
        name="Brasil Tech Summit 2025",
        organizer="Brasil Events",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        expected_audience_size=10000,
        official_website_url="https://example.com/brasil-summit",
        brief_description="A major Brazilian technology summit.",
        start_date="2027-10-01",
        end_date="2027-10-03",
        duration_days=3,
        location=LocationModel(
            venue_name="SP Expo",
            full_street_address="Rua Teste, 100",
            city="São Paulo",
            state_province="São Paulo",
            country="Brazil",
            postal_code="04329-900",
            continent="South America",
        ),
        companies=[
            CompanyModel(name="Brasil Events", role=CompanyRole.ORGANIZER),
            CompanyModel(name="AWS", role=CompanyRole.SPONSOR),
            CompanyModel(name="Google", role=CompanyRole.SPONSOR),
        ],
        source_url="https://example.com/brasil-summit",
        source_name="test_source",
        source_confidence=0.9,
    )


@pytest.fixture
def client(tmp_db):
    """Create a FastAPI test client with temporary database.

    Args:
        tmp_db: Temporary Database fixture.

    Yields:
        TestClient for the app.
    """
    from app import database as db_module
    original_db = db_module.db
    db_module.db = tmp_db

    from app.routes import health as health_mod
    from app.routes import events as events_mod
    from app.routes import admin as admin_mod
    health_mod.db = tmp_db
    events_mod.db = tmp_db
    admin_mod.db = tmp_db

    with TestClient(app) as c:
        yield c

    db_module.db = original_db
    health_mod.db = original_db
    events_mod.db = original_db
    admin_mod.db = original_db
