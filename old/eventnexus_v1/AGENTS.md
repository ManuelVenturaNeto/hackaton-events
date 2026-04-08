<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# eventnexus_v1 (Full-Stack Implementation)

## Purpose
Most complete reference implementation of the Event Mapper. Full-stack application with a FastAPI Python backend and a React/TypeScript frontend. This is the **primary reference** for the active implementation — patterns, data models, and architecture here should be reused. **Read-only.**

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI Python backend — event discovery, normalization, scoring, API routes (see `backend/AGENTS.md`) |
| `frontend/` | React + TypeScript frontend — event explorer UI with hooks, services, and typed API client (see `frontend/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- **Read-only** — reference only
- `backend/` is the authoritative source for: data models, repository pattern, service layer architecture, and API contract
- `frontend/` defines the Event type interface that the backend `EventResponse` model must match exactly
- The backend uses SQLite locally; active implementation targets Supabase/PostgreSQL

## Dependencies

### External
- Python 3.x / FastAPI / SQLAlchemy — backend
- React 18 / TypeScript / Vite — frontend
- SQLite — local development database (Supabase PostgreSQL in production)

<!-- MANUAL: -->
