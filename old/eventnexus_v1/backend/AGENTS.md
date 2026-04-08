<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# backend (eventnexus_v1)

## Purpose
FastAPI Python backend for the Event Mapper. Implements event discovery from multiple sources, normalization, scoring, deduplication, and a REST API. Uses the repository pattern with a service layer. **Read-only reference.**

## Key Files

| File | Description |
|------|-------------|
| `app/main.py` | FastAPI app entry point — lifespan, CORS, router registration |
| `app/config.py` | Settings via Pydantic BaseSettings (env vars) |
| `app/database.py` | Database initialization and SQLAlchemy session management |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `app/models/` | Pydantic models — EventCreate, EventResponse, LocationModel, enums |
| `app/repositories/` | Data access layer — event_repository, sync_run_repository |
| `app/services/` | Business logic — discovery_service, normalization_service, scoring_service |
| `app/routes/` | API route handlers — events, admin, health |
| `app/sources/` | Data source abstractions — base_source, web_search_source, curated_source |
| `tests/` | Pytest test suite — routes, normalization, scoring, deduplication, repository, database |

## For AI Agents

### Working In This Directory
- **Read-only** — copy patterns into active implementation, never modify here
- The `EventResponse` model in `app/models/event.py` defines the frontend contract — field names use camelCase to match the React `Event` interface
- `discovery_service.py` orchestrates all sources; individual sources inherit from `base_source.py`

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/events` | List upcoming events (sorted by networkingRelevance desc, startDate asc) |
| GET | `/api/events/{event_id}` | Single event detail |
| POST | `/api/events/sync` | Trigger sync — returns operational summary, not event data |

### Data Flow
```
POST /sync
  → discovery_service: fetch from all sources
  → normalization_service: clean and standardize
  → scoring_service: compute networkingRelevanceScore
  → deduplication: remove duplicates
  → event_repository: upsert to DB

GET /events
  → event_repository: read from DB (no live web queries)
```

### Event Categories
`Technology`, `Banking / Financial`, `Agribusiness / Agriculture`, `Medical / Healthcare`, `Business / Entrepreneurship`

### Testing Requirements
- Run with pytest from `backend/` directory
- `tests/conftest.py` sets up fixtures
- Key test files: `test_routes.py`, `test_normalization.py`, `test_scoring.py`, `test_deduplication.py`

### Common Patterns
- Repository pattern: repositories only do DB operations, services contain business logic
- All settings via environment variables (Pydantic BaseSettings)
- Async lifespan context manager for DB init/teardown

## Dependencies

### Internal
- `app/models/` — shared data contracts between layers

### External
- FastAPI — web framework
- SQLAlchemy — ORM
- Pydantic — data validation and settings
- pytest — testing

<!-- MANUAL: -->
