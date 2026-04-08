<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# eventnexus (Early Prototype)

## Purpose
First prototype of the Event Mapper — a React + TypeScript + Vite application with SSR (server-side rendering) via `server.ts`. The frontend includes event discovery UI components and a server-side event aggregation/processing layer. **Read-only reference.**

## Key Files

| File | Description |
|------|-------------|
| `server.ts` | SSR entry point — Vite SSR server with event aggregation |
| `vite.config.ts` | Vite build configuration with SSR setup |
| `tsconfig.json` | TypeScript configuration |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `components/` | React UI components: EventCard, EventDetails, SearchBar, FilterSidebar |
| `server/` | Server-side logic: eventAggregator, eventProcessor |

## For AI Agents

### Working In This Directory
- **Read-only** — do not modify any files here
- Useful for understanding early component design decisions (EventCard structure, filter UX)
- The SSR approach was abandoned in favor of a separate backend API in `eventnexus_v1/`

### Common Patterns
- Component props defined as TypeScript interfaces above the component
- Search and filter state managed locally in components

## Dependencies

### External
- React 18 — UI
- Vite — build + SSR
- TypeScript — type safety

<!-- MANUAL: -->
