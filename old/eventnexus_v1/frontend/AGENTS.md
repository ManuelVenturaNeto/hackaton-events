<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# frontend (eventnexus_v1)

## Purpose
React + TypeScript + Vite frontend for the Event Mapper. Implements event browsing UI with typed API client, custom hooks, and service layer. The `Event` type interface defined here is the **contract that the backend `EventResponse` model must satisfy**. **Read-only reference.**

## Key Files

| File | Description |
|------|-------------|
| `types/event.ts` | Core `Event` TypeScript interface — single source of truth for the data contract |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `components/` | Reusable UI components — EventCard, Badge |
| `pages/` | Page-level components — EventExplorer, EventDetails |
| `hooks/` | Custom React hooks — useEvent, useEvents |
| `api/` | Typed API client — eventsApi (wraps fetch calls to backend) |
| `services/` | Business logic — eventsService (filtering, sorting, transformation) |
| `utils/` | Utilities — cache helpers |

## For AI Agents

### Working In This Directory
- **Read-only** — copy patterns into active implementation, never modify here
- The `Event` interface in `types/event.ts` uses camelCase field names — the backend `EventResponse` must match exactly
- Hooks (`useEvent`, `useEvents`) are the primary data-fetching mechanism for pages

### Architecture Layers
```
pages/       ← route-level views, compose hooks + components
hooks/       ← data fetching and state management
services/    ← business logic (filter, sort, transform)
api/         ← raw HTTP calls to backend
types/       ← shared TypeScript interfaces
components/  ← pure presentational components
```

### Common Patterns
- `useEvents` hook fetches the full list; `useEvent` fetches single by ID
- `eventsService` handles client-side sorting and filtering on top of API data
- Components receive typed props matching `Event` or sub-interfaces

## Dependencies

### Internal
- Backend API at `GET /api/events` and `GET /api/events/{id}`

### External
- React 18 — UI framework
- TypeScript — type safety
- Vite — build tool

<!-- MANUAL: -->
