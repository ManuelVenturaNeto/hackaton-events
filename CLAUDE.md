# CLAUDE.md — EventNexus Project

## Project Overview

EventNexus is a corporate event mapper for the Brazilian travel market. It has two sub-projects:

- **`eventnexus/`** — Python FastAPI backend (API + event aggregation)
- **`eventnexus-frontend/`** — React 19 SPA (Vite + Tailwind)
- **`old/`** — Reference code from v1, not used in production

## Commands

### Backend

```bash
cd eventnexus
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000     # dev server
python -m pytest tests/ -v                     # run tests (needs PostgreSQL)
docker compose up                              # full local stack
```

### Frontend

```bash
cd eventnexus-frontend
npm install
npm run dev          # Vite dev server (port 5173)
npm run build        # production build to dist/
npm run lint         # TypeScript check
```

## Architecture

### Backend layers

```
Routes (health.py, events.py)
  -> Services (discovery, normalization, scoring)
    -> Repositories (event_repository, sync_run_repository)
      -> PostgreSQL (Supabase)
  -> Sources (curated, ticketmaster, eventbrite, sympla, web_search)
```

### Key patterns

- **Deduplication:** composite key `lower(name)|lower(organizer)|start_date|lower(city)|lower(country)|lower(url)`
- **Sync:** `POST /api/events/sync` runs in FastAPI BackgroundTasks, returns immediately
- **Scoring:** deterministic 0-100 score (audience + companies + category + format + duration + brazil bonus)
- **Migrations:** SQL files in `eventnexus/migrations/`, run on startup via `db.initialize()`, idempotent with `IF NOT EXISTS`

### Frontend patterns

- All text in Portuguese (pt-BR)
- Types in `src/types.ts` match the API EventResponse contract exactly
- API base URL configurable via `VITE_API_URL` env var
- Onfly brand identity: Poppins font, blue palette, pill buttons, glassmorphic cards

## Code Style

### Python (backend)

- No docstrings needed on simple/obvious functions
- Use type hints
- snake_case for everything except Pydantic model fields that face the frontend (camelCase)
- `psycopg2` with `%s` placeholders (never f-strings in SQL)

### TypeScript (frontend)

- Functional components only
- Named exports for components, default export for App
- Tailwind utility classes, custom classes defined in index.css `@layer components`
- date-fns with `ptBR` locale for all date formatting

## Environment

- Python 3.11+ (backend)
- Node 18+ (frontend, Node 20+ recommended for native Tailwind)
- PostgreSQL 16 (local via Docker or Supabase)
- Git commits to `main` branch, tag `frontend` tracks latest frontend commit

## Testing

- Backend unit tests: `pytest tests/test_normalization.py tests/test_scoring.py` (no DB needed)
- Backend integration tests: `pytest tests/test_repository.py tests/test_routes.py` (needs PostgreSQL at localhost:5432)
- Frontend: no test suite yet, verify with `npm run build` and `npm run lint`

## Important Files

- `docs/superpowers/specs/2026-04-08-eventnexus-api-design.md` — design spec
- `docs/superpowers/plans/2026-04-08-eventnexus-api-implementation.md` — backend plan
- `docs/superpowers/plans/2026-04-08-eventnexus-frontend.md` — frontend plan
- `eventnexus/.env.example` — backend env template
- `eventnexus-frontend/.env.example` — frontend env template
