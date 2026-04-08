"""Shared test fixtures."""

import os

import psycopg2
import psycopg2.extras
import pytest

from app.database import Database
from app.models.event import (
    CompanyModel,
    CompanyRole,
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/eventnexus_test",
)


@pytest.fixture(scope="session")
def create_test_db():
    """Create the test database if it doesn't exist."""
    base_url = TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
    try:
        conn = psycopg2.connect(base_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'eventnexus_test'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE eventnexus_test")
        cur.close()
        conn.close()
    except psycopg2.OperationalError:
        pytest.skip("PostgreSQL not available for testing")


@pytest.fixture
def test_db(create_test_db):
    """Provide a clean database for each test."""
    database = Database(database_url=TEST_DB_URL)
    database.initialize()
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM event_sources")
    cur.execute("DELETE FROM event_companies")
    cur.execute("DELETE FROM event_locations")
    cur.execute("DELETE FROM sync_runs")
    cur.execute("DELETE FROM events")
    conn.commit()
    cur.close()
    yield database
    database.close()


@pytest.fixture
def sample_event() -> EventCreate:
    return EventCreate(
        name="Test Tech Conference 2026",
        organizer="Test Corp",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        expected_audience_size=5000,
        official_website_url="https://example.com/test-conf",
        brief_description="A test technology conference.",
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
    return EventCreate(
        name="Brasil Tech Summit 2026",
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
