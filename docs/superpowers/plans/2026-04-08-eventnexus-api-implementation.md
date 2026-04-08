# EventNexus API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend that aggregates corporate events from 5 sources (curated list, Ticketmaster API, Eventbrite API, Sympla scraper, web scraper) into a Supabase PostgreSQL database and serves them via REST endpoints.

**Architecture:** Layered — Routes → Services → Repositories → PostgreSQL. Sources fetch raw events, services normalize/score them, repositories handle persistence with deduplication. Sync runs in background via FastAPI BackgroundTasks.

**Tech Stack:** Python 3.11+, FastAPI 0.115.6, psycopg2-binary (PostgreSQL driver), httpx, BeautifulSoup4, pydantic-settings, Docker Compose for local dev.

**IMPORTANT RULE:** Each task ends with a git commit to main describing what was completed.

---

## File Structure

```
/home/robson/code/hackaton/eventnexus/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + lifespan + migrations
│   ├── config.py                   # Settings via pydantic-settings
│   ├── database.py                 # PostgreSQL connection manager
│   ├── models/
│   │   ├── __init__.py
│   │   └── event.py                # Pydantic schemas + enums
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── event_repository.py     # Event CRUD + upsert + dedup
│   │   └── sync_run_repository.py  # Sync run tracking
│   ├── services/
│   │   ├── __init__.py
│   │   ├── discovery_service.py    # Orchestrates sync pipeline
│   │   ├── normalization_service.py # Country/date/field normalization
│   │   └── scoring_service.py      # Networking relevance scoring
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base_source.py          # Abstract source interface
│   │   ├── curated_source.py       # ~35 hardcoded real events
│   │   ├── ticketmaster_source.py  # Ticketmaster Discovery API
│   │   ├── eventbrite_source.py    # Eventbrite Search API
│   │   ├── sympla_scraper.py       # Sympla web scraping
│   │   └── web_search_source.py    # 10times + confs.tech scraping
│   └── routes/
│       ├── __init__.py
│       ├── health.py               # GET /api/health
│       └── events.py               # GET/POST /api/events/*
├── migrations/
│   ├── 001_create_tables.sql
│   └── 002_create_indexes.sql
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_scoring.py
│   ├── test_normalization.py
│   ├── test_repository.py
│   └── test_routes.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── pytest.ini
```

---

### Task 1: Project Scaffold & Config

**Files:**
- Create: `eventnexus/requirements.txt`
- Create: `eventnexus/.env.example`
- Create: `eventnexus/pytest.ini`
- Create: `eventnexus/app/__init__.py`
- Create: `eventnexus/app/models/__init__.py`
- Create: `eventnexus/app/repositories/__init__.py`
- Create: `eventnexus/app/services/__init__.py`
- Create: `eventnexus/app/sources/__init__.py`
- Create: `eventnexus/app/routes/__init__.py`
- Create: `eventnexus/tests/__init__.py`
- Create: `eventnexus/app/config.py`

- [ ] **Step 1: Create project directory and requirements.txt**

```bash
mkdir -p /home/robson/code/hackaton/eventnexus/{app/{models,repositories,services,sources,routes},migrations,tests}
```

Create `eventnexus/requirements.txt`:
```
fastapi==0.115.6
uvicorn==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
psycopg2-binary==2.9.10
httpx==0.28.1
beautifulsoup4==4.12.3
lxml==5.3.0
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Create .env.example**

Create `eventnexus/.env.example`:
```env
# Database (local Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eventnexus

# For Supabase (production) - uncomment and fill password
# DATABASE_URL=postgresql://postgres.prvljsmnyxvvgzmvsgzz:[YOUR-PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# API Keys
TICKETMASTER_API_KEY=
EVENTBRITE_API_TOKEN=

# App
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
MAX_CONCURRENT_FETCHES=10
REQUEST_TIMEOUT_SECONDS=30
```

- [ ] **Step 3: Create pytest.ini**

Create `eventnexus/pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
```

- [ ] **Step 4: Create __init__.py files**

Create empty `__init__.py` in: `app/`, `app/models/`, `app/repositories/`, `app/services/`, `app/sources/`, `app/routes/`, `tests/`.

- [ ] **Step 5: Create app/config.py**

Create `eventnexus/app/config.py`:
```python
"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/eventnexus"
    ticketmaster_api_key: str = ""
    eventbrite_api_token: str = ""
    max_concurrent_fetches: int = 10
    request_timeout_seconds: int = 30
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]


settings = Settings()
```

- [ ] **Step 6: Verify setup**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && pip install -r requirements.txt && python -c "from app.config import settings; print(settings.database_url)"
```
Expected: prints the default DATABASE_URL string.

- [ ] **Step 7: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/
git commit -m "feat(eventnexus): scaffold project with config, requirements, and directory structure"
```

---

### Task 2: Database Layer & Migrations

**Files:**
- Create: `eventnexus/migrations/001_create_tables.sql`
- Create: `eventnexus/migrations/002_create_indexes.sql`
- Create: `eventnexus/app/database.py`

- [ ] **Step 1: Create 001_create_tables.sql**

Create `eventnexus/migrations/001_create_tables.sql`:
```sql
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    organizer VARCHAR(300),
    category VARCHAR(50),
    format VARCHAR(20),
    status VARCHAR(20) DEFAULT 'upcoming',
    expected_audience_size INTEGER,
    official_website_url TEXT,
    brief_description TEXT,
    networking_relevance_score FLOAT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    duration_days INTEGER DEFAULT 1,
    dedup_key VARCHAR(500) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    venue_name VARCHAR(300),
    full_street_address TEXT,
    city VARCHAR(200),
    state_province VARCHAR(200),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    continent VARCHAR(50),
    neighborhood VARCHAR(200),
    street VARCHAR(300),
    street_number VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS event_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    role VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS event_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    source_name VARCHAR(100),
    source_url TEXT,
    confidence FLOAT DEFAULT 0,
    fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(30) DEFAULT 'running',
    events_discovered INTEGER DEFAULT 0,
    events_inserted INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb
);
```

- [ ] **Step 2: Create 002_create_indexes.sql**

Create `eventnexus/migrations/002_create_indexes.sql`:
```sql
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_score ON events(networking_relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_locations_country ON event_locations(country);
CREATE INDEX IF NOT EXISTS idx_locations_city ON event_locations(city);
CREATE INDEX IF NOT EXISTS idx_companies_event ON event_companies(event_id);
CREATE INDEX IF NOT EXISTS idx_sources_event ON event_sources(event_id);
```

- [ ] **Step 3: Create app/database.py**

Create `eventnexus/app/database.py`:
```python
"""PostgreSQL database connection manager for Supabase."""

import logging
from pathlib import Path

import psycopg2
import psycopg2.extras

from app.config import settings

logger = logging.getLogger(__name__)

# Register UUID adapter so psycopg2 returns UUIDs as strings
psycopg2.extras.register_uuid()


class Database:
    """PostgreSQL connection manager."""

    def __init__(self, database_url: str = settings.database_url) -> None:
        self.database_url = database_url
        self._conn = None

    def get_connection(self):
        """Get or create a database connection.

        Returns:
            A psycopg2 connection with RealDictCursor.
        """
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self._conn.autocommit = False
        return self._conn

    def initialize(self) -> None:
        """Run all migration SQL files in order."""
        conn = self.get_connection()
        migrations_dir = Path(__file__).parent.parent / "migrations"
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            logger.info("Running migration: %s", sql_file.name)
            conn.cursor().execute(sql_file.read_text())
        conn.commit()
        logger.info("Database migrations completed.")

    def is_reachable(self) -> bool:
        """Check if the database is reachable."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None


db = Database()
```

- [ ] **Step 4: Verify migrations parse correctly**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from pathlib import Path
for f in sorted(Path('migrations').glob('*.sql')):
    print(f'OK: {f.name} ({len(f.read_text())} chars)')
"
```
Expected: prints OK for both migration files.

- [ ] **Step 5: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/migrations/ eventnexus/app/database.py
git commit -m "feat(eventnexus): add PostgreSQL database layer and migration scripts"
```

---

### Task 3: Pydantic Models

**Files:**
- Create: `eventnexus/app/models/event.py`

- [ ] **Step 1: Create app/models/event.py**

Create `eventnexus/app/models/event.py`:
```python
"""Pydantic models for events, matching the frontend contract."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    TECHNOLOGY = "Technology"
    BANKING_FINANCIAL = "Banking / Financial"
    AGRIBUSINESS = "Agribusiness / Agriculture"
    MEDICAL = "Medical / Healthcare"
    BUSINESS = "Business / Entrepreneurship"


class EventFormat(str, Enum):
    IN_PERSON = "in-person"
    HYBRID = "hybrid"
    ONLINE = "online"


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    CANCELED = "canceled"
    POSTPONED = "postponed"
    COMPLETED = "completed"


class CompanyRole(str, Enum):
    ORGANIZER = "organizer"
    SPONSOR = "sponsor"
    EXHIBITOR = "exhibitor"
    PARTNER = "partner"
    FEATURED = "featured"


class LocationModel(BaseModel):
    venue_name: str = ""
    full_street_address: str = ""
    city: str = ""
    state_province: str = ""
    country: str = ""
    postal_code: str = ""
    continent: str = ""
    neighborhood: str = ""
    street: str = ""
    street_number: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompanyModel(BaseModel):
    name: str
    role: CompanyRole


class SourceModel(BaseModel):
    source_name: str = Field(alias="sourceName", default="")
    confidence: float = 0.0

    model_config = {"populate_by_name": True}


class EventCreate(BaseModel):
    """Internal model for creating/updating events."""
    name: str
    organizer: str
    category: EventCategory
    format: EventFormat
    status: EventStatus = EventStatus.UPCOMING
    expected_audience_size: int = 0
    official_website_url: str = ""
    brief_description: str = ""
    networking_relevance_score: float = 0.0
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    location: LocationModel = Field(default_factory=LocationModel)
    companies: list[CompanyModel] = Field(default_factory=list)
    source_url: str = ""
    source_name: str = ""
    source_confidence: float = 1.0


class LocationResponse(BaseModel):
    """Location in camelCase for frontend."""
    venueName: str = ""
    fullStreetAddress: str = ""
    city: str = ""
    stateProvince: str = ""
    country: str = ""
    postalCode: str = ""
    continent: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompanyResponse(BaseModel):
    name: str
    role: str


class SourceResponse(BaseModel):
    sourceName: str = ""
    confidence: float = 0.0


class EventResponse(BaseModel):
    """Event response matching the frontend contract (camelCase)."""
    id: str
    name: str
    organizer: str
    category: str
    format: str
    status: str
    expectedAudienceSize: int
    officialWebsiteUrl: str
    briefDescription: str
    networkingRelevanceScore: float
    startDate: str
    endDate: str
    durationDays: int
    lastUpdated: str
    location: LocationResponse
    companiesInvolved: list[CompanyResponse]
    sources: list[SourceResponse] = Field(default_factory=list)


class SyncStartResponse(BaseModel):
    """Response for POST /api/events/sync."""
    status: str
    runId: str
    message: str
```

- [ ] **Step 2: Verify models import**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.models.event import EventCreate, EventResponse, EventCategory, LocationModel, CompanyModel, CompanyRole
e = EventCreate(name='Test', organizer='Org', category=EventCategory.TECHNOLOGY, format='in-person')
print(f'OK: {e.name}, category={e.category.value}')
"
```
Expected: `OK: Test, category=Technology`

- [ ] **Step 3: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/models/
git commit -m "feat(eventnexus): add Pydantic models with camelCase response contract"
```

---

### Task 4: Normalization Service + Tests

**Files:**
- Create: `eventnexus/app/services/normalization_service.py`
- Create: `eventnexus/tests/test_normalization.py`

- [ ] **Step 1: Write failing test**

Create `eventnexus/tests/test_normalization.py`:
```python
"""Tests for the normalization service."""

from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.services.normalization_service import NormalizationService


def _make_event(**overrides) -> EventCreate:
    defaults = dict(
        name="  Test Event  ",
        organizer="  Test Org  ",
        category=EventCategory.TECHNOLOGY,
        format=EventFormat.IN_PERSON,
        status=EventStatus.UPCOMING,
        brief_description="  A description  ",
        official_website_url="https://example.com/event/",
        start_date="2026-09-15",
        end_date="2026-09-17",
        duration_days=0,
        location=LocationModel(country="brasil", city="São Paulo"),
    )
    defaults.update(overrides)
    return EventCreate(**defaults)


class TestNormalizationService:
    def setup_method(self):
        self.svc = NormalizationService()

    def test_trims_whitespace(self):
        event = self.svc.normalize(_make_event())
        assert event.name == "Test Event"
        assert event.organizer == "Test Org"
        assert event.brief_description == "A description"

    def test_strips_trailing_slash_from_url(self):
        event = self.svc.normalize(_make_event())
        assert event.official_website_url == "https://example.com/event"

    def test_normalizes_country_alias(self):
        event = self.svc.normalize(_make_event())
        assert event.location.country == "Brazil"

    def test_infers_continent(self):
        event = self.svc.normalize(_make_event())
        assert event.location.continent == "South America"

    def test_calculates_duration(self):
        event = self.svc.normalize(_make_event())
        assert event.duration_days == 3  # Sep 15-17 = 3 days

    def test_duration_minimum_one(self):
        event = self.svc.normalize(_make_event(start_date="", end_date="", duration_days=0))
        assert event.duration_days == 1

    def test_preserves_existing_continent(self):
        event = self.svc.normalize(
            _make_event(location=LocationModel(country="Brazil", continent="Already Set"))
        )
        assert event.location.continent == "Already Set"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_normalization.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.normalization_service'`

- [ ] **Step 3: Implement normalization service**

Create `eventnexus/app/services/normalization_service.py`:
```python
"""Service for normalizing event data before persistence."""

import logging
from datetime import datetime

from app.models.event import EventCreate

logger = logging.getLogger(__name__)

COUNTRY_ALIASES = {
    "united states": "USA",
    "united states of america": "USA",
    "us": "USA",
    "u.s.a.": "USA",
    "united kingdom": "UK",
    "great britain": "UK",
    "england": "UK",
    "brasil": "Brazil",
    "deutschland": "Germany",
    "españa": "Spain",
    "emirates": "UAE",
    "united arab emirates": "UAE",
}

COUNTRY_TO_CONTINENT = {
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "North America",
    "Brazil": "South America",
    "Argentina": "South America",
    "Chile": "South America",
    "Colombia": "South America",
    "UK": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Spain": "Europe",
    "Portugal": "Europe",
    "Italy": "Europe",
    "Netherlands": "Europe",
    "Switzerland": "Europe",
    "China": "Asia",
    "Japan": "Asia",
    "India": "Asia",
    "Singapore": "Asia",
    "UAE": "Asia",
    "Israel": "Asia",
    "South Korea": "Asia",
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    "South Africa": "Africa",
    "Nigeria": "Africa",
}


class NormalizationService:
    """Normalizes raw event data into clean, consistent format."""

    def normalize(self, event: EventCreate) -> EventCreate:
        """Normalize an event's data fields."""
        event.name = event.name.strip()
        event.organizer = event.organizer.strip()
        event.brief_description = event.brief_description.strip()
        event.official_website_url = event.official_website_url.strip().rstrip("/")

        country_lower = event.location.country.strip().lower()
        if country_lower in COUNTRY_ALIASES:
            event.location.country = COUNTRY_ALIASES[country_lower]

        if not event.location.continent:
            event.location.continent = COUNTRY_TO_CONTINENT.get(
                event.location.country, ""
            )

        if event.start_date and event.end_date and event.duration_days == 0:
            event.duration_days = self._calc_duration(event.start_date, event.end_date)

        if event.duration_days < 1:
            event.duration_days = 1

        return event

    def _calc_duration(self, start: str, end: str) -> int:
        """Calculate duration in days between ISO date strings."""
        try:
            s = datetime.fromisoformat(start)
            e = datetime.fromisoformat(end)
            return max(1, (e - s).days + 1)
        except (ValueError, TypeError):
            return 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_normalization.py -v
```
Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/services/normalization_service.py eventnexus/tests/test_normalization.py
git commit -m "feat(eventnexus): add normalization service with country aliases and duration calc"
```

---

### Task 5: Scoring Service + Tests

**Files:**
- Create: `eventnexus/app/services/scoring_service.py`
- Create: `eventnexus/tests/test_scoring.py`

- [ ] **Step 1: Write failing test**

Create `eventnexus/tests/test_scoring.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_scoring.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.scoring_service'`

- [ ] **Step 3: Implement scoring service**

Create `eventnexus/app/services/scoring_service.py`:
```python
"""Service for calculating networking relevance scores."""

import logging

from app.models.event import EventCreate

logger = logging.getLogger(__name__)

AUDIENCE_TIERS = [
    (100000, 30),
    (50000, 27),
    (20000, 24),
    (10000, 20),
    (5000, 15),
    (1000, 10),
    (0, 5),
]


class ScoringService:
    """Calculates networking relevance scores for events (0-100)."""

    def calculate_score(self, event: EventCreate) -> float:
        """Calculate the networking relevance score for an event."""
        score = 0.0

        # Audience size (0-30)
        for threshold, points in AUDIENCE_TIERS:
            if event.expected_audience_size >= threshold:
                score += points
                break

        # Company diversity (0-25)
        num_companies = len(event.companies)
        if num_companies >= 10:
            score += 25
        elif num_companies >= 5:
            score += 20
        elif num_companies >= 3:
            score += 15
        elif num_companies >= 1:
            score += 10

        # Category relevance (0-15)
        category_scores = {
            "Technology": 15,
            "Banking / Financial": 13,
            "Business / Entrepreneurship": 12,
            "Medical / Healthcare": 11,
            "Agribusiness / Agriculture": 10,
        }
        score += category_scores.get(event.category.value, 10)

        # Format bonus (0-10)
        format_scores = {
            "in-person": 10,
            "hybrid": 8,
            "online": 4,
        }
        score += format_scores.get(event.format.value, 5)

        # Duration bonus (0-10)
        if event.duration_days >= 4:
            score += 10
        elif event.duration_days >= 3:
            score += 8
        elif event.duration_days >= 2:
            score += 6
        else:
            score += 3

        # Brazil strategic bonus (0-10)
        if event.location.country.lower() == "brazil":
            score += 10

        return min(100.0, round(score, 1))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_scoring.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/services/scoring_service.py eventnexus/tests/test_scoring.py
git commit -m "feat(eventnexus): add networking relevance scoring service"
```

---

### Task 6: Repositories (Event + SyncRun)

**Files:**
- Create: `eventnexus/app/repositories/event_repository.py`
- Create: `eventnexus/app/repositories/sync_run_repository.py`
- Create: `eventnexus/tests/conftest.py`
- Create: `eventnexus/tests/test_repository.py`

- [ ] **Step 1: Create test fixtures (conftest.py)**

Create `eventnexus/tests/conftest.py`:
```python
"""Shared test fixtures."""

import os
import subprocess

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


@pytest.fixture(scope="session", autouse=True)
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
    # Clean tables before each test
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
```

- [ ] **Step 2: Write failing repository tests**

Create `eventnexus/tests/test_repository.py`:
```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_repository.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.repositories.event_repository'`

- [ ] **Step 4: Implement event_repository.py**

Create `eventnexus/app/repositories/event_repository.py`:
```python
"""Repository for event CRUD operations on PostgreSQL."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import Database
from app.models.event import (
    CompanyResponse,
    EventCreate,
    EventResponse,
    LocationModel,
    LocationResponse,
    SourceResponse,
    CompanyModel,
)

logger = logging.getLogger(__name__)


class EventRepository:
    """Handles all event persistence operations against PostgreSQL."""

    def __init__(self, database: Database) -> None:
        self.db = database

    def _generate_dedup_key(self, event: EventCreate) -> str:
        parts = [
            event.name.strip().lower(),
            event.organizer.strip().lower(),
            event.start_date.strip(),
            event.location.city.strip().lower(),
            event.location.country.strip().lower(),
        ]
        if event.official_website_url:
            parts.append(event.official_website_url.strip().lower().rstrip("/"))
        return "|".join(parts)

    def upsert_event(self, event: EventCreate) -> tuple[str, bool]:
        """Insert or update an event using deduplication.

        Returns:
            Tuple of (event_id, was_inserted).
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        dedup_key = self._generate_dedup_key(event)

        cur.execute("SELECT id FROM events WHERE dedup_key = %s", (dedup_key,))
        existing = cur.fetchone()

        if existing:
            event_id = str(existing["id"])
            cur.execute(
                """UPDATE events SET
                    name=%s, organizer=%s, category=%s, format=%s, status=%s,
                    expected_audience_size=%s, official_website_url=%s,
                    brief_description=%s, networking_relevance_score=%s,
                    start_date=%s, end_date=%s, duration_days=%s, last_updated=%s
                WHERE id=%s""",
                (
                    event.name, event.organizer, event.category.value,
                    event.format.value, event.status.value,
                    event.expected_audience_size, event.official_website_url,
                    event.brief_description, event.networking_relevance_score,
                    event.start_date or None, event.end_date or None,
                    event.duration_days, now, event_id,
                ),
            )
            self._upsert_location(cur, event_id, event.location)
            self._replace_companies(cur, event_id, event.companies)
            self._add_source(cur, event_id, event.source_name, event.source_url, event.source_confidence, now)
            conn.commit()
            return event_id, False

        event_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO events
                (id, name, organizer, category, format, status,
                 expected_audience_size, official_website_url,
                 brief_description, networking_relevance_score,
                 start_date, end_date, duration_days,
                 last_updated, created_at, dedup_key)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id, event.name, event.organizer, event.category.value,
                event.format.value, event.status.value,
                event.expected_audience_size, event.official_website_url,
                event.brief_description, event.networking_relevance_score,
                event.start_date or None, event.end_date or None,
                event.duration_days, now, now, dedup_key,
            ),
        )
        self._upsert_location(cur, event_id, event.location)
        self._replace_companies(cur, event_id, event.companies)
        self._add_source(cur, event_id, event.source_name, event.source_url, event.source_confidence, now)
        conn.commit()
        return event_id, True

    def _upsert_location(self, cur, event_id: str, loc: LocationModel) -> None:
        cur.execute("DELETE FROM event_locations WHERE event_id = %s", (event_id,))
        cur.execute(
            """INSERT INTO event_locations
                (event_id, venue_name, full_street_address, city, state_province,
                 country, postal_code, continent, neighborhood, street,
                 street_number, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event_id, loc.venue_name, loc.full_street_address, loc.city,
                loc.state_province, loc.country, loc.postal_code, loc.continent,
                loc.neighborhood, loc.street, loc.street_number,
                loc.latitude, loc.longitude,
            ),
        )

    def _replace_companies(self, cur, event_id: str, companies: list[CompanyModel]) -> None:
        cur.execute("DELETE FROM event_companies WHERE event_id = %s", (event_id,))
        for company in companies:
            cur.execute(
                "INSERT INTO event_companies (event_id, name, role) VALUES (%s,%s,%s)",
                (event_id, company.name, company.role.value),
            )

    def _add_source(self, cur, event_id: str, source_name: str, source_url: str, confidence: float, fetched_at: str) -> None:
        if source_name:
            cur.execute(
                """INSERT INTO event_sources (event_id, source_name, source_url, confidence, fetched_at)
                VALUES (%s,%s,%s,%s,%s)""",
                (event_id, source_name, source_url, confidence, fetched_at),
            )

    def update_status(self, event_id: str, new_status: str) -> bool:
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "UPDATE events SET status=%s, last_updated=%s WHERE id=%s",
            (new_status, now, event_id),
        )
        conn.commit()
        return cur.rowcount > 0

    def get_event_by_id(self, event_id: str) -> Optional[EventResponse]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_response(cur, row)

    def list_events(
        self,
        search: str = "",
        category: str = "",
        country: str = "",
        city: str = "",
        status: str = "",
        format_: str = "",
        start_date_from: str = "",
        start_date_to: str = "",
        min_audience_size: Optional[int] = None,
        sort_by: str = "networkingRelevance",
        sort_order: str = "desc",
    ) -> list[EventResponse]:
        conn = self.db.get_connection()
        cur = conn.cursor()

        query = """
            SELECT e.* FROM events e
            LEFT JOIN event_locations l ON e.id = l.event_id
        """
        conditions = []
        params: list = []

        # Default: only upcoming, exclude past events
        if not status:
            conditions.append("LOWER(e.status) = 'upcoming'")
        else:
            conditions.append("LOWER(e.status) = LOWER(%s)")
            params.append(status)

        conditions.append("(e.end_date IS NULL OR e.end_date >= CURRENT_DATE)")

        if search:
            conditions.append(
                "(LOWER(e.name) LIKE %s OR LOWER(e.organizer) LIKE %s OR LOWER(e.brief_description) LIKE %s)"
            )
            term = f"%{search.lower()}%"
            params.extend([term, term, term])

        if category:
            conditions.append("LOWER(e.category) = LOWER(%s)")
            params.append(category)

        if country:
            conditions.append("LOWER(l.country) = LOWER(%s)")
            params.append(country)

        if city:
            conditions.append("LOWER(l.city) = LOWER(%s)")
            params.append(city)

        if format_:
            conditions.append("LOWER(e.format) = LOWER(%s)")
            params.append(format_)

        if start_date_from:
            conditions.append("e.start_date >= %s")
            params.append(start_date_from)

        if start_date_to:
            conditions.append("e.start_date <= %s")
            params.append(start_date_to)

        if min_audience_size is not None:
            conditions.append("e.expected_audience_size >= %s")
            params.append(min_audience_size)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_map = {
            "networkingRelevance": "e.networking_relevance_score",
            "startDate": "e.start_date",
            "audienceSize": "e.expected_audience_size",
            "lastUpdated": "e.last_updated",
        }
        sort_col = sort_map.get(sort_by, "e.networking_relevance_score")
        direction = "ASC" if sort_order == "asc" else "DESC"

        # Default sort: networkingRelevance DESC, then startDate ASC
        if sort_by == "networkingRelevance":
            query += f" ORDER BY {sort_col} {direction}, e.start_date ASC"
        else:
            query += f" ORDER BY {sort_col} {direction}"

        query += " LIMIT 500"

        cur.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_response(cur, row) for row in rows]

    def get_all_event_ids_and_urls(self) -> list[dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, official_website_url, status FROM events")
        return [dict(r) for r in cur.fetchall()]

    def get_event_count(self) -> int:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM events")
        return cur.fetchone()["cnt"]

    def _row_to_response(self, cur, row: dict) -> EventResponse:
        event_id = str(row["id"])

        cur.execute("SELECT * FROM event_locations WHERE event_id = %s", (event_id,))
        loc = cur.fetchone()

        location = LocationResponse(
            venueName=loc["venue_name"] if loc else "",
            fullStreetAddress=loc["full_street_address"] if loc else "",
            city=loc["city"] if loc else "",
            stateProvince=loc["state_province"] if loc else "",
            country=loc["country"] if loc else "",
            postalCode=loc["postal_code"] if loc else "",
            continent=loc["continent"] if loc else "",
            latitude=loc["latitude"] if loc else None,
            longitude=loc["longitude"] if loc else None,
        )

        cur.execute("SELECT name, role FROM event_companies WHERE event_id = %s", (event_id,))
        companies = [CompanyResponse(name=c["name"], role=c["role"]) for c in cur.fetchall()]

        cur.execute("SELECT source_name, confidence FROM event_sources WHERE event_id = %s", (event_id,))
        sources = [SourceResponse(sourceName=s["source_name"], confidence=s["confidence"]) for s in cur.fetchall()]

        return EventResponse(
            id=event_id,
            name=row["name"],
            organizer=row["organizer"] or "",
            category=row["category"] or "",
            format=row["format"] or "",
            status=row["status"] or "",
            expectedAudienceSize=row["expected_audience_size"] or 0,
            officialWebsiteUrl=row["official_website_url"] or "",
            briefDescription=row["brief_description"] or "",
            networkingRelevanceScore=row["networking_relevance_score"] or 0,
            startDate=str(row["start_date"] or ""),
            endDate=str(row["end_date"] or ""),
            durationDays=row["duration_days"] or 1,
            lastUpdated=str(row["last_updated"] or ""),
            location=location,
            companiesInvolved=companies,
            sources=sources,
        )
```

- [ ] **Step 5: Implement sync_run_repository.py**

Create `eventnexus/app/repositories/sync_run_repository.py`:
```python
"""Repository for sync run tracking."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import Database

logger = logging.getLogger(__name__)


class SyncRunRepository:
    """Tracks sync/populate/refresh operations in PostgreSQL."""

    def __init__(self, database: Database) -> None:
        self.db = database

    def start_run(self, run_type: str) -> str:
        """Record the start of a sync run. Returns the run UUID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sync_runs (run_type, status) VALUES (%s, %s) RETURNING id",
            (run_type, "running"),
        )
        run_id = str(cur.fetchone()["id"])
        conn.commit()
        return run_id

    def complete_run(
        self,
        run_id: str,
        status: str = "completed",
        events_discovered: int = 0,
        events_inserted: int = 0,
        events_updated: int = 0,
        errors: Optional[list[str]] = None,
    ) -> None:
        conn = self.db.get_connection()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """UPDATE sync_runs SET
                completed_at=%s, status=%s, events_discovered=%s,
                events_inserted=%s, events_updated=%s, errors=%s
            WHERE id=%s""",
            (
                now, status, events_discovered, events_inserted,
                events_updated, json.dumps(errors or []), run_id,
            ),
        )
        conn.commit()

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
```

- [ ] **Step 6: Run repository tests**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_repository.py -v
```
Expected: all 9 tests PASS (requires local PostgreSQL running).

- [ ] **Step 7: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/repositories/ eventnexus/tests/conftest.py eventnexus/tests/test_repository.py
git commit -m "feat(eventnexus): add event and sync_run repositories for PostgreSQL"
```

---

### Task 7: Base Source + Curated Source

**Files:**
- Create: `eventnexus/app/sources/base_source.py`
- Create: `eventnexus/app/sources/curated_source.py`

- [ ] **Step 1: Create base_source.py**

Create `eventnexus/app/sources/base_source.py`:
```python
"""Base class for event source adapters."""

from abc import ABC, abstractmethod

from app.models.event import EventCreate


class BaseEventSource(ABC):
    """Abstract base class for all event source adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable source name."""

    @abstractmethod
    def fetch_events(self) -> list[EventCreate]:
        """Fetch events from this source."""

    @abstractmethod
    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        """Check if an event's status has changed.

        Returns new status string if changed, or None.
        """
```

- [ ] **Step 2: Create curated_source.py**

Copy the curated source from `old/eventnexus_v1/backend/app/sources/curated_source.py` into `eventnexus/app/sources/curated_source.py`. This file contains ~35 hardcoded real events. The implementation is identical — no database dependencies, pure data.

Run:
```bash
cp /home/robson/code/hackaton/old/eventnexus_v1/backend/app/sources/curated_source.py \
   /home/robson/code/hackaton/eventnexus/app/sources/curated_source.py
```

- [ ] **Step 3: Verify curated source loads**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.sources.curated_source import CuratedEventSource
src = CuratedEventSource()
events = src.fetch_events()
print(f'OK: {len(events)} curated events loaded')
print(f'First: {events[0].name}')
"
```
Expected: `OK: 35 curated events loaded` (approximately).

- [ ] **Step 4: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/base_source.py eventnexus/app/sources/curated_source.py
git commit -m "feat(eventnexus): add base source interface and curated event source (~35 events)"
```

---

### Task 8: Ticketmaster Source

**Files:**
- Create: `eventnexus/app/sources/ticketmaster_source.py`

- [ ] **Step 1: Create ticketmaster_source.py**

Create `eventnexus/app/sources/ticketmaster_source.py`:
```python
"""Ticketmaster Discovery API source adapter."""

import logging
from datetime import datetime, timedelta

import httpx

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource

logger = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# Map Ticketmaster classifications to our categories
CLASSIFICATION_MAP = {
    "technology": EventCategory.TECHNOLOGY,
    "science": EventCategory.TECHNOLOGY,
    "business": EventCategory.BUSINESS,
    "finance": EventCategory.BANKING_FINANCIAL,
    "health": EventCategory.MEDICAL,
    "agriculture": EventCategory.AGRIBUSINESS,
}

# Search keywords for corporate/professional events
SEARCH_KEYWORDS = [
    "conference",
    "summit",
    "expo",
    "congress",
    "forum",
    "tech",
    "business",
]


class TicketmasterSource(BaseEventSource):
    """Fetches events from the Ticketmaster Discovery API."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    @property
    def name(self) -> str:
        return "ticketmaster"

    def fetch_events(self) -> list[EventCreate]:
        if not settings.ticketmaster_api_key:
            logger.warning("TICKETMASTER_API_KEY not set, skipping source")
            return []

        all_events: list[EventCreate] = []
        now = datetime.utcnow()
        end = now + timedelta(days=180)

        for keyword in SEARCH_KEYWORDS:
            try:
                events = self._search(keyword, now, end)
                all_events.extend(events)
            except Exception as exc:
                logger.warning("Ticketmaster search '%s' failed: %s", keyword, exc)

        logger.info("Ticketmaster: fetched %d events total", len(all_events))
        return all_events

    def _search(self, keyword: str, start: datetime, end: datetime) -> list[EventCreate]:
        params = {
            "apikey": settings.ticketmaster_api_key,
            "keyword": keyword,
            "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "size": 100,
            "sort": "date,asc",
        }

        response = self._client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        embedded = data.get("_embedded", {})
        raw_events = embedded.get("events", [])

        results = []
        for raw in raw_events:
            parsed = self._parse_event(raw)
            if parsed:
                results.append(parsed)

        return results

    def _parse_event(self, raw: dict) -> EventCreate | None:
        try:
            name = raw.get("name", "")
            if not name:
                return None

            # Dates
            dates = raw.get("dates", {}).get("start", {})
            start_date = dates.get("localDate", "")
            end_date = raw.get("dates", {}).get("end", {}).get("localDate", start_date)

            # Venue/Location
            venues = raw.get("_embedded", {}).get("venues", [{}])
            venue = venues[0] if venues else {}
            venue_name = venue.get("name", "")
            city = venue.get("city", {}).get("name", "")
            state = venue.get("state", {}).get("name", "")
            country = venue.get("country", {}).get("name", "")
            postal = venue.get("postalCode", "")
            address = venue.get("address", {}).get("line1", "")
            lat = None
            lng = None
            loc_data = venue.get("location", {})
            if loc_data:
                lat = float(loc_data.get("latitude", 0)) or None
                lng = float(loc_data.get("longitude", 0)) or None

            # Category
            classifications = raw.get("classifications", [{}])
            segment = (classifications[0].get("segment", {}).get("name", "") if classifications else "").lower()
            genre = (classifications[0].get("genre", {}).get("name", "") if classifications else "").lower()
            category = EventCategory.TECHNOLOGY
            for key, cat in CLASSIFICATION_MAP.items():
                if key in segment or key in genre:
                    category = cat
                    break

            # URL
            url = raw.get("url", "")

            # Description
            info = raw.get("info", "") or raw.get("pleaseNote", "") or ""

            return EventCreate(
                name=name,
                organizer=raw.get("promoter", {}).get("name", "Unknown"),
                category=category,
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=url,
                brief_description=info[:500],
                start_date=start_date,
                end_date=end_date or start_date,
                location=LocationModel(
                    venue_name=venue_name,
                    full_street_address=address,
                    city=city,
                    state_province=state,
                    country=country,
                    postal_code=postal,
                    latitude=lat,
                    longitude=lng,
                ),
                companies=[],
                source_url=url,
                source_name="ticketmaster",
                source_confidence=0.80,
            )
        except Exception as exc:
            logger.debug("Failed to parse Ticketmaster event: %s", exc)
            return None

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.sources.ticketmaster_source import TicketmasterSource
src = TicketmasterSource()
print(f'OK: source name = {src.name}')
"
```
Expected: `OK: source name = ticketmaster`

- [ ] **Step 3: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/ticketmaster_source.py
git commit -m "feat(eventnexus): add Ticketmaster Discovery API source adapter"
```

---

### Task 9: Eventbrite Source

**Files:**
- Create: `eventnexus/app/sources/eventbrite_source.py`

- [ ] **Step 1: Create eventbrite_source.py**

Create `eventnexus/app/sources/eventbrite_source.py`:
```python
"""Eventbrite API source adapter."""

import logging
from datetime import datetime, timedelta

import httpx

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource

logger = logging.getLogger(__name__)

BASE_URL = "https://www.eventbriteapi.com/v3"

CATEGORY_MAP = {
    "101": EventCategory.BUSINESS,       # Business & Professional
    "102": EventCategory.TECHNOLOGY,      # Science & Technology
    "111": EventCategory.BANKING_FINANCIAL,  # Charity & Causes (closest)
    "117": EventCategory.TECHNOLOGY,      # Science & Tech (alt)
}

SEARCH_QUERIES = [
    {"q": "technology conference", "location.address": "Brazil"},
    {"q": "business summit", "location.address": "Brazil"},
    {"q": "tech expo", "location.address": "Brazil"},
    {"q": "fintech conference", "location.address": "Brazil"},
    {"q": "healthcare congress", "location.address": "Brazil"},
]


class EventbriteSource(BaseEventSource):
    """Fetches events from the Eventbrite API."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    @property
    def name(self) -> str:
        return "eventbrite"

    def fetch_events(self) -> list[EventCreate]:
        if not settings.eventbrite_api_token:
            logger.warning("EVENTBRITE_API_TOKEN not set, skipping source")
            return []

        all_events: list[EventCreate] = []
        now = datetime.utcnow()
        end = now + timedelta(days=180)

        headers = {"Authorization": f"Bearer {settings.eventbrite_api_token}"}

        for search in SEARCH_QUERIES:
            try:
                params = {
                    **search,
                    "start_date.range_start": now.strftime("%Y-%m-%dT%H:%M:%S"),
                    "start_date.range_end": end.strftime("%Y-%m-%dT%H:%M:%S"),
                    "expand": "venue,organizer",
                }
                response = self._client.get(
                    f"{BASE_URL}/events/search/",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                for raw in data.get("events", []):
                    parsed = self._parse_event(raw)
                    if parsed:
                        all_events.append(parsed)
            except Exception as exc:
                logger.warning("Eventbrite search failed for %s: %s", search.get("q"), exc)

        logger.info("Eventbrite: fetched %d events total", len(all_events))
        return all_events

    def _parse_event(self, raw: dict) -> EventCreate | None:
        try:
            name = raw.get("name", {}).get("text", "")
            if not name:
                return None

            description = raw.get("description", {}).get("text", "") or ""
            url = raw.get("url", "")

            # Dates
            start = raw.get("start", {})
            end = raw.get("end", {})
            start_date = start.get("local", "")[:10] if start.get("local") else ""
            end_date = end.get("local", "")[:10] if end.get("local") else start_date

            # Venue
            venue = raw.get("venue", {}) or {}
            address = venue.get("address", {}) or {}
            city = address.get("city", "")
            state = address.get("region", "")
            country = address.get("country", "")
            lat = float(address.get("latitude", 0)) or None
            lng = float(address.get("longitude", 0)) or None

            # Organizer
            organizer = raw.get("organizer", {}) or {}
            organizer_name = organizer.get("name", "Unknown")

            # Capacity
            capacity = raw.get("capacity", 0) or 0

            # Online check
            is_online = raw.get("online_event", False)
            event_format = EventFormat.ONLINE if is_online else EventFormat.IN_PERSON

            # Category inference from name/description
            category = self._infer_category(name, description)

            return EventCreate(
                name=name,
                organizer=organizer_name,
                category=category,
                format=event_format,
                status=EventStatus.UPCOMING,
                expected_audience_size=capacity,
                official_website_url=url,
                brief_description=description[:500],
                start_date=start_date,
                end_date=end_date,
                location=LocationModel(
                    venue_name=venue.get("name", ""),
                    full_street_address=address.get("localized_address_display", ""),
                    city=city,
                    state_province=state,
                    country=country,
                    latitude=lat,
                    longitude=lng,
                ),
                companies=[],
                source_url=url,
                source_name="eventbrite",
                source_confidence=0.80,
            )
        except Exception as exc:
            logger.debug("Failed to parse Eventbrite event: %s", exc)
            return None

    def _infer_category(self, name: str, description: str) -> EventCategory:
        text = (name + " " + description).lower()
        if any(kw in text for kw in ["bank", "financ", "fintech", "payment", "money"]):
            return EventCategory.BANKING_FINANCIAL
        if any(kw in text for kw in ["agri", "farm", "crop", "agriculture"]):
            return EventCategory.AGRIBUSINESS
        if any(kw in text for kw in ["health", "medical", "pharma", "hospital"]):
            return EventCategory.MEDICAL
        if any(kw in text for kw in ["business", "entrepreneur", "startup", "retail"]):
            return EventCategory.BUSINESS
        return EventCategory.TECHNOLOGY

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.sources.eventbrite_source import EventbriteSource
src = EventbriteSource()
print(f'OK: source name = {src.name}')
"
```
Expected: `OK: source name = eventbrite`

- [ ] **Step 3: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/eventbrite_source.py
git commit -m "feat(eventnexus): add Eventbrite API source adapter"
```

---

### Task 10: Sympla Scraper + Web Search Source

**Files:**
- Create: `eventnexus/app/sources/sympla_scraper.py`
- Create: `eventnexus/app/sources/web_search_source.py`

- [ ] **Step 1: Create sympla_scraper.py**

Create `eventnexus/app/sources/sympla_scraper.py`:
```python
"""Sympla web scraper source adapter."""

import logging
import re
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models.event import (
    EventCategory,
    EventCreate,
    EventFormat,
    EventStatus,
    LocationModel,
)
from app.sources.base_source import BaseEventSource

logger = logging.getLogger(__name__)

SYMPLA_URLS = [
    {
        "url": "https://www.sympla.com.br/eventos/tecnologia-inovacao",
        "name": "sympla_tech",
        "category": EventCategory.TECHNOLOGY,
    },
    {
        "url": "https://www.sympla.com.br/eventos/negocios-empreendedorismo",
        "name": "sympla_business",
        "category": EventCategory.BUSINESS,
    },
    {
        "url": "https://www.sympla.com.br/eventos/saude-bem-estar",
        "name": "sympla_health",
        "category": EventCategory.MEDICAL,
    },
]


class SymplaScraperSource(BaseEventSource):
    """Scrapes event listings from Sympla."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; EventNexus/1.0)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "pt-BR,pt;q=0.9",
            },
        )

    @property
    def name(self) -> str:
        return "sympla"

    def fetch_events(self) -> list[EventCreate]:
        all_events: list[EventCreate] = []

        for source in SYMPLA_URLS:
            try:
                response = self._client.get(source["url"])
                response.raise_for_status()
                events = self._parse_page(response.text, source)
                all_events.extend(events)
                logger.info("Sympla %s: %d events", source["name"], len(events))
            except Exception as exc:
                logger.warning("Sympla %s failed: %s", source["name"], exc)

        logger.info("Sympla: fetched %d events total", len(all_events))
        return all_events

    def _parse_page(self, html: str, source: dict) -> list[EventCreate]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        cards = soup.select(
            "[class*='event-card'], [class*='EventCard'], "
            "[class*='event-item'], a[href*='/evento/']"
        )

        for card in cards[:50]:
            event = self._parse_card(card, source)
            if event:
                events.append(event)

        return events

    def _parse_card(self, card, source: dict) -> Optional[EventCreate]:
        try:
            name_el = card.select_one("h3, h2, h4, [class*='title'], [class*='name']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                return None

            date_el = card.select_one("[class*='date'], time, [class*='when']")
            date_text = date_el.get_text(strip=True) if date_el else ""
            start_date, end_date = self._parse_dates(date_text)

            loc_el = card.select_one("[class*='location'], [class*='venue'], [class*='where']")
            location_text = loc_el.get_text(strip=True) if loc_el else ""

            link = card.get("href") or ""
            if not link:
                a = card.select_one("a[href]")
                link = a.get("href", "") if a else ""
            if link and not link.startswith("http"):
                link = f"https://www.sympla.com.br{link}"

            city = ""
            state = ""
            if location_text:
                parts = [p.strip() for p in location_text.split(",")]
                city = parts[0] if parts else ""
                state = parts[1] if len(parts) > 1 else ""

            return EventCreate(
                name=name,
                organizer="Unknown",
                category=source["category"],
                format=EventFormat.IN_PERSON,
                status=EventStatus.UPCOMING,
                expected_audience_size=0,
                official_website_url=link,
                brief_description="",
                start_date=start_date,
                end_date=end_date or start_date,
                location=LocationModel(
                    city=city,
                    state_province=state,
                    country="Brazil",
                    continent="South America",
                ),
                companies=[],
                source_url=source["url"],
                source_name="sympla",
                source_confidence=0.50,
            )
        except Exception as exc:
            logger.debug("Failed to parse Sympla card: %s", exc)
            return None

    def _parse_dates(self, text: str) -> tuple[str, str]:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if len(dates) >= 2:
            return dates[0], dates[1]
        if len(dates) == 1:
            return dates[0], dates[0]
        return "", ""

    def check_event_status(self, event_name: str, event_url: str) -> str | None:
        return None

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 2: Copy and adapt web_search_source.py**

Copy from old project and ensure import paths are correct:
```bash
cp /home/robson/code/hackaton/old/eventnexus_v1/backend/app/sources/web_search_source.py \
   /home/robson/code/hackaton/eventnexus/app/sources/web_search_source.py
```

The file has no database dependencies — only uses `app.config.settings` and `app.models.event`, which exist in the new project with identical interfaces.

- [ ] **Step 3: Verify both sources import**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.sources.sympla_scraper import SymplaScraperSource
from app.sources.web_search_source import WebSearchSource
print(f'OK: sympla={SymplaScraperSource().name}, web_search={WebSearchSource().name}')
"
```
Expected: `OK: sympla=sympla, web_search=web_search`

- [ ] **Step 4: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/sources/sympla_scraper.py eventnexus/app/sources/web_search_source.py
git commit -m "feat(eventnexus): add Sympla scraper and generic web search source"
```

---

### Task 11: Discovery Service (Sync Orchestration)

**Files:**
- Create: `eventnexus/app/services/discovery_service.py`

- [ ] **Step 1: Create discovery_service.py**

Create `eventnexus/app/services/discovery_service.py`:
```python
"""Service orchestrating event discovery from multiple sources."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from app.config import settings
from app.database import Database
from app.models.event import EventCreate
from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository
from app.services.normalization_service import NormalizationService
from app.services.scoring_service import ScoringService
from app.sources.curated_source import CuratedEventSource
from app.sources.eventbrite_source import EventbriteSource
from app.sources.sympla_scraper import SymplaScraperSource
from app.sources.ticketmaster_source import TicketmasterSource
from app.sources.web_search_source import WebSearchSource

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Orchestrates the full event discovery pipeline."""

    def __init__(self, database: Database) -> None:
        self.event_repo = EventRepository(database)
        self.sync_repo = SyncRunRepository(database)
        self.normalizer = NormalizationService()
        self.scorer = ScoringService()
        self.sources = [
            CuratedEventSource(),
            TicketmasterSource(),
            EventbriteSource(),
            SymplaScraperSource(),
            WebSearchSource(),
        ]

    def sync(self) -> dict:
        """Run full sync: fetch from all sources, normalize, score, persist.

        Returns dict with operation summary.
        """
        run_id = self.sync_repo.start_run("sync")
        errors: list[str] = []
        all_events: list[EventCreate] = []

        # Fetch from all sources
        for source in self.sources:
            try:
                events = source.fetch_events()
                all_events.extend(events)
                logger.info("Source '%s': %d events", source.name, len(events))
            except Exception as exc:
                error_msg = f"Source '{source.name}' failed: {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Filter out past events
        today = date.today().isoformat()
        all_events = [
            e for e in all_events
            if not e.end_date or e.end_date >= today
        ]

        # Normalize, score, persist
        inserted = 0
        updated = 0
        for event in all_events:
            try:
                normalized = self.normalizer.normalize(event)
                normalized.networking_relevance_score = self.scorer.calculate_score(normalized)
                _, was_new = self.event_repo.upsert_event(normalized)
                if was_new:
                    inserted += 1
                else:
                    updated += 1
            except Exception as exc:
                error_msg = f"Failed to persist '{event.name}': {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        status = "completed" if not errors else "completed_with_errors"
        self.sync_repo.complete_run(
            run_id,
            status=status,
            events_discovered=len(all_events),
            events_inserted=inserted,
            events_updated=updated,
            errors=errors,
        )

        return {
            "status": status,
            "runId": run_id,
            "eventsDiscovered": len(all_events),
            "eventsInserted": inserted,
            "eventsUpdated": updated,
            "errors": errors,
            "message": f"Discovered {len(all_events)} events. Inserted {inserted}, updated {updated}.",
        }
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -c "
from app.services.discovery_service import DiscoveryService
print('OK: DiscoveryService imported')
"
```
Expected: `OK: DiscoveryService imported`

- [ ] **Step 3: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/services/discovery_service.py
git commit -m "feat(eventnexus): add discovery service orchestrating 5 event sources"
```

---

### Task 12: FastAPI Routes + Main App

**Files:**
- Create: `eventnexus/app/routes/health.py`
- Create: `eventnexus/app/routes/events.py`
- Create: `eventnexus/app/main.py`
- Create: `eventnexus/tests/test_routes.py`

- [ ] **Step 1: Create health.py route**

Create `eventnexus/app/routes/health.py`:
```python
"""Health check route."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import db

router = APIRouter()


@router.get("/api/health")
def health_check() -> dict:
    db_ok = db.is_reachable()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 2: Create events.py route**

Create `eventnexus/app/routes/events.py`:
```python
"""Event API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.database import db
from app.models.event import EventResponse, SyncStartResponse
from app.repositories.event_repository import EventRepository
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events")


def _get_repo() -> EventRepository:
    return EventRepository(db)


def _run_sync() -> None:
    """Background task: run full sync."""
    try:
        service = DiscoveryService(db)
        result = service.sync()
        logger.info("Background sync completed: %s", result["message"])
    except Exception as exc:
        logger.error("Background sync failed: %s", exc)


@router.get("", response_model=list[EventResponse])
def list_events(
    search: str = Query("", description="Free-text search"),
    category: str = Query("", description="Filter by category"),
    country: str = Query("", description="Filter by country"),
    city: str = Query("", description="Filter by city"),
    status: str = Query("", description="Filter by status"),
    format: str = Query("", description="Filter by format"),
    startDateFrom: str = Query("", description="Min start date"),
    startDateTo: str = Query("", description="Max start date"),
    minAudienceSize: Optional[int] = Query(None, description="Min audience"),
    sortBy: str = Query("networkingRelevance", description="Sort field"),
    sortOrder: str = Query("desc", description="Sort order"),
) -> list[EventResponse]:
    repo = _get_repo()
    return repo.list_events(
        search=search,
        category=category,
        country=country,
        city=city,
        status=status,
        format_=format,
        start_date_from=startDateFrom,
        start_date_to=startDateTo,
        min_audience_size=minAudienceSize,
        sort_by=sortBy,
        sort_order=sortOrder,
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str) -> EventResponse:
    repo = _get_repo()
    event = repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/sync", response_model=SyncStartResponse)
def sync_events(background_tasks: BackgroundTasks) -> SyncStartResponse:
    """Trigger event synchronization in background."""
    from app.repositories.sync_run_repository import SyncRunRepository
    sync_repo = SyncRunRepository(db)
    run_id = sync_repo.start_run("sync")

    background_tasks.add_task(_run_sync)

    return SyncStartResponse(
        status="sync_started",
        runId=run_id,
        message="Synchronization started in background",
    )
```

- [ ] **Step 3: Create main.py**

Create `eventnexus/app/main.py`:
```python
"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db
from app.routes import events, health

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    db.initialize()
    logger.info("Application started. Database initialized.")
    yield
    db.close()
    logger.info("Application shutdown.")


app = FastAPI(
    title="EventNexus API",
    description="Corporate travel event mapper for the Brazilian market.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(events.router)
```

- [ ] **Step 4: Write route tests**

Create `eventnexus/tests/test_routes.py`:
```python
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
```

- [ ] **Step 5: Run route tests**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/test_routes.py -v
```
Expected: all 5 tests PASS (requires local PostgreSQL).

- [ ] **Step 6: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/app/routes/ eventnexus/app/main.py eventnexus/tests/test_routes.py
git commit -m "feat(eventnexus): add FastAPI routes (health, events, sync) with BackgroundTasks"
```

---

### Task 13: Docker Compose & Dockerfile

**Files:**
- Create: `eventnexus/Dockerfile`
- Create: `eventnexus/docker-compose.yml`

- [ ] **Step 1: Create Dockerfile**

Create `eventnexus/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**

Create `eventnexus/docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: eventnexus
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/eventnexus
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

- [ ] **Step 3: Verify Docker Compose config parses**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && docker compose config --quiet 2>&1 && echo "OK: config valid" || echo "WARN: docker compose not available, skip"
```
Expected: `OK: config valid` (or skip if Docker not available).

- [ ] **Step 4: Commit**

```bash
cd /home/robson/code/hackaton
git add eventnexus/Dockerfile eventnexus/docker-compose.yml
git commit -m "feat(eventnexus): add Dockerfile and docker-compose for local development"
```

---

### Task 14: Final Integration Test & Smoke Check

**Files:**
- No new files — verify everything works together.

- [ ] **Step 1: Run all tests**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && python -m pytest tests/ -v
```
Expected: all tests PASS.

- [ ] **Step 2: Start server locally and test endpoints**

Run:
```bash
cd /home/robson/code/hackaton/eventnexus && timeout 5 uvicorn app.main:app --port 8000 2>&1 || true
```

Then test each endpoint:
```bash
curl -s http://localhost:8000/api/health | python -m json.tool
curl -s http://localhost:8000/api/events | python -m json.tool
curl -s -X POST http://localhost:8000/api/events/sync | python -m json.tool
```

Expected:
- `/api/health` returns `{"status": "healthy", "database": "connected", ...}`
- `/api/events` returns `[]` (empty until sync runs)
- `/api/events/sync` returns `{"status": "sync_started", "runId": "...", ...}`

- [ ] **Step 3: Verify OpenAPI docs**

Run:
```bash
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print('Endpoints:', list(d['paths'].keys()))"
```
Expected: `Endpoints: ['/api/health', '/api/events', '/api/events/{event_id}', '/api/events/sync']`

- [ ] **Step 4: Final commit**

```bash
cd /home/robson/code/hackaton
git add -A
git commit -m "feat(eventnexus): complete EventNexus API v2 - all endpoints, sources, and tests"
git push origin main
```

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Scaffold & Config | requirements.txt, .env.example, config.py, __init__.py files |
| 2 | Database & Migrations | database.py, 001_create_tables.sql, 002_create_indexes.sql |
| 3 | Pydantic Models | models/event.py |
| 4 | Normalization Service | services/normalization_service.py + tests |
| 5 | Scoring Service | services/scoring_service.py + tests |
| 6 | Repositories | repositories/event_repository.py, sync_run_repository.py + tests |
| 7 | Base + Curated Source | sources/base_source.py, curated_source.py |
| 8 | Ticketmaster Source | sources/ticketmaster_source.py |
| 9 | Eventbrite Source | sources/eventbrite_source.py |
| 10 | Sympla + Web Scraper | sources/sympla_scraper.py, web_search_source.py |
| 11 | Discovery Service | services/discovery_service.py |
| 12 | Routes + Main App | routes/health.py, events.py, main.py + tests |
| 13 | Docker | Dockerfile, docker-compose.yml |
| 14 | Integration & Smoke | End-to-end verification |
