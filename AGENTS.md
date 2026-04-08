<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# hackaton-events

## Purpose
Hackathon project focused on corporate travel intelligence. Contains two product tracks: an **Event Mapper** (aggregates Brazilian business events for corporate travelers) and a **Duty of Care** API (travel risk scoring by country). The `src/` directory holds active development specs and plans; `old/` archives two prior prototype implementations used as reference code.

## Key Files

| File | Description |
|------|-------------|
| `.gitignore` | Git ignore rules |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `src/` | Active development — specs, plans, and assets (see `src/AGENTS.md`) |
| `old/` | Archived prototype implementations for reference (see `old/AGENTS.md`) |
| `.claude/` | Claude Code framework config and OnFly OAuth MCP skill (see `.claude/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- `src/` is the canonical source of truth for current work; treat `old/` as read-only reference
- The project has two parallel product tracks — keep Duty of Care and Event Mapper concerns separate
- Deploy target: **GCP Cloud Run** (backend) with Supabase/PostgreSQL as the primary database for Event Mapper; Firestore + BigQuery for Duty of Care

### Testing Requirements
- Backend: pytest (see `old/eventnexus_v1/backend/tests/` for patterns)
- Frontend: No test setup yet in active branch; follow existing React patterns from `old/eventnexus_v1/frontend/`

### Common Patterns
- FastAPI for all Python backends
- React + TypeScript + Vite for frontends
- Environment variables for secrets (never hardcode credentials)

## Dependencies

### External
- Python 3.12 / FastAPI — backend framework
- React 18 / TypeScript / Vite — frontend framework
- Supabase (PostgreSQL via pgBouncer) — Event Mapper database
- GCP Cloud Run + Cloud Build — deployment
- GCP Firestore + BigQuery — Duty of Care caching and logging

<!-- MANUAL: -->
