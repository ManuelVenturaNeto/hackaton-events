# NetworkX Backend - Event Discovery API

## Architecture

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings (env vars)
│   ├── database.py                # SQLite connection manager
│   ├── models/
│   │   └── event.py               # Pydantic models (matches frontend contract)
│   ├── repositories/
│   │   ├── event_repository.py    # Event CRUD with deduplication
│   │   └── sync_run_repository.py # Sync operation tracking
│   ├── services/
│   │   ├── discovery_service.py   # Orchestrates full discovery pipeline
│   │   ├── normalization_service.py # Country/date/field normalization
│   │   └── scoring_service.py     # Networking relevance scoring
│   ├── sources/
│   │   ├── base_source.py         # Abstract source interface
│   │   ├── curated_source.py      # Pre-researched real events
│   │   └── web_search_source.py   # Web scraping discovery
│   └── routes/
│       ├── health.py              # GET /api/health
│       ├── events.py              # Event CRUD + populate/refresh/sync
│       └── admin.py               # GET /api/admin/sync-runs, /stats
└── tests/                         # Pytest test suite (44 tests)
```

## Database Schema

### events
Main event table. `dedup_key` is a UNIQUE composite of normalized name + organizer + start_date + city + country + URL.

### event_locations
One-to-one with events. Stores venue, address, city, state, country, continent, lat/lng.

### event_companies
Many-to-one with events. Each row: company name + role (organizer/sponsor/exhibitor/partner/featured).

### event_sources
Many-to-one with events. Tracks which source provided the data, with confidence score and fetch timestamp.

### sync_runs
Operational log of every populate/refresh/sync operation.

## Public API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (API + DB) |
| GET | `/api/events` | List events with filters and sorting |
| GET | `/api/events/{id}` | Get single event detail |
| POST | `/api/events/populate` | Discover and persist new events |
| POST | `/api/events/refresh-status` | Check existing events for status changes |
| POST | `/api/events/sync` | Run populate + refresh-status sequentially |
| GET | `/api/admin/sync-runs` | View recent sync operation logs |
| GET | `/api/admin/stats` | Database statistics |

### Filtering (GET /api/events)
`search`, `category`, `continent`, `country`, `stateProvince`, `city`, `status`, `format`, `organizer`, `company`, `startDateFrom`, `startDateTo`, `endDateFrom`, `endDateTo`, `minAudienceSize`, `maxAudienceSize`

### Sorting
`sortBy`: networkingRelevance, startDate, audienceSize, companiesCount, lastUpdated
`sortOrder`: asc, desc

## Discovery Strategy

### Populate Flow
1. **CuratedEventSource**: Pre-researched real events from official websites (35+ events: 20 global + 15 Brazil)
2. **WebSearchSource**: Concurrent HTTP scraping of event aggregator sites (10times.com, confs.tech)
3. **NormalizationService**: Standardizes country names, calculates duration, infers continent
4. **ScoringService**: Calculates networking relevance (0-100) based on audience, companies, format, duration, Brazil bonus
5. **EventRepository.upsert_event()**: Deduplicates via composite key, inserts or updates

### Global Search
- Major tech conferences: AWS re:Invent, Google Cloud Next, Microsoft Ignite, NVIDIA GTC, CES
- Industry events: Hannover Messe, GITEX, Web Summit, Collision, MWC
- Financial: Money20/20, Sibos
- Health: HIMSS
- Agriculture: World Agri-Tech
- Web scraping: 10times.com/technology/conferences, confs.tech

### Brazil-Specific Search (Deeper Coverage)
- Banking: FEBRABAN TECH, CIAB FEBRABAN
- Technology: FUTURECOM, Web Summit Rio, Campus Party Brasil
- Agriculture: Agrishow, TecnoAgro, Expo Agro Digital
- Health: Hospitalar, ABIMED Summit, Brazil Health Show
- Business: Gramado Summit, APAS Show, Latam Retail Show, E-Commerce Brasil
- Web scraping: 10times.com/brazil/technology, banking-finance, agriculture, medical-pharma

### How Official Pages Are Prioritized
- CuratedSource events all link to official event websites (confidence 0.85-0.95)
- WebSearchSource extracts URLs from event listings and checks for official domains
- During upsert, the most recent source data overwrites previous data
- Source confidence is tracked per source record

### Deduplication
Deterministic composite key: `lower(name)|lower(organizer)|start_date|lower(city)|lower(country)|lower(url)`
- Same event from multiple sources = single record
- Case-insensitive matching
- URL normalized (trailing slash removed)

### Event Status Detection
- Curated source maintains known statuses
- Web check fetches the event's official page and searches for "cancel", "postpone", "reschedul" keywords
- Status changes are persisted immediately

### Audience Size / Company Involvement
- Curated events: researched from official event pages (marked as confidence 0.85-0.95)
- Web-scraped events: extracted from HTML if available, defaults to 0 (not estimated)
- Scoring treats audience=0 as minimum tier, not as estimated

### Authoritative vs Estimated Fields
- **Authoritative**: name, organizer, dates, location (city/country), URL, category, format
- **Estimated**: audience size (from source, may vary), networking score (calculated), duration (calculated from dates if missing)

## Concurrency Strategy

**ThreadPoolExecutor** is used in two places:
1. **WebSearchSource.fetch_events()**: Each source URL is fetched in a separate thread (max_workers=10)
2. **DiscoveryService.refresh_status()**: Each event's official page is checked concurrently

This is I/O-bound work (HTTP requests), so threading is appropriate.
The executor is created per-operation and torn down after completion.

### What Runs Daily vs On-Demand
- **Daily**: `POST /api/events/populate` (discover new) + `POST /api/events/refresh-status` (check changes)
- **On-demand**: `POST /api/events/sync` (combined), or individual routes
- The frontend sync button triggers `POST /api/events/sync`

## Running Locally

```bash
cd backend
pip install -r requirements.txt

# Start the API server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Populate the database with events
curl -X POST http://localhost:8000/api/events/populate

# Check events
curl http://localhost:8000/api/events

# Refresh status
curl -X POST http://localhost:8000/api/events/refresh-status
```

## Running Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

## Daily Execution

Trigger daily with cron or a scheduler:
```bash
# Discover new events and check status changes
curl -X POST http://localhost:8000/api/events/sync
```

Or run each step separately:
```bash
curl -X POST http://localhost:8000/api/events/populate
curl -X POST http://localhost:8000/api/events/refresh-status
```

## Tradeoffs and Assumptions

1. **SQLite vs PostgreSQL**: SQLite is used for simplicity and zero-config deployment. WAL mode enables concurrent reads. For production scale, migrate to PostgreSQL.
2. **Curated seed data**: Real events are pre-researched rather than purely scraped, ensuring quality baseline. Web scraping supplements this.
3. **Web scraping fragility**: HTML parsers depend on site structure. Sites may block or change. Curated source provides a reliable fallback.
4. **Scoring is deterministic**: No ML model; scoring uses a transparent point system documented in scoring_service.py.
5. **Single-node**: No distributed architecture. ThreadPoolExecutor provides concurrency within a single process.
6. **No authentication**: API is public. Add auth middleware if needed.
