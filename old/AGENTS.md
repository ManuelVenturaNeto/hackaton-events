<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# old

## Purpose
Archive of two prior prototype implementations of the Event Mapper. These are **read-only reference code** — do not modify. Use them as architectural and pattern reference when building the active implementation in `../src/`.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `eventnexus/` | Early prototype — React + TypeScript + Vite SSR frontend with server-side event aggregation (see `eventnexus/AGENTS.md`) |
| `eventnexus_v1/` | Full-stack implementation — FastAPI backend + React frontend, more complete and production-closer (see `eventnexus_v1/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Treat everything here as **read-only reference** — never edit these files
- `eventnexus_v1/` is the more complete and production-ready reference; prefer it over `eventnexus/`
- When extracting patterns, copy them into the active `src/` implementation rather than modifying here

### Common Patterns
- Backend patterns: FastAPI, SQLAlchemy, repository pattern, service layer
- Frontend patterns: React hooks, typed API clients, component decomposition

<!-- MANUAL: -->
