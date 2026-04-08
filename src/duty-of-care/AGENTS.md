<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# duty-of-care

## Purpose
Duty of Care travel risk API — specifications and implementation plans. This API aggregates public travel risk data sources and returns a normalized composite risk score (0–100) per country with categorical breakdown. Designed for deployment on GCP Cloud Run.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `specs/` | Technical design documents for the API |
| `plans/` | Implementation and execution plans |

## For AI Agents

### Working In This Directory
- Read `specs/2026-04-06-duty-of-care-api-design.md` before implementing anything in this track
- The API has three endpoints: `GET /risk/{country_code}`, `GET /advisories/{country_code}`, `GET /health`
- Each data collector is **independent** — failures must not crash the API (graceful degradation via `asyncio.gather`)

### Architecture Overview
```
FastAPI (Cloud Run)
  → collectors: State Dept (always), Open-Meteo (always), GDELT (always)
                Amadeus GeoSure (optional), ACLED (optional)
  → scorer: weighted composite from available sources
  → cache: Firestore (in-memory fallback locally)
  → logs: BigQuery (fire-and-forget)
```

### External Data Sources
| Source | Credentials | Category |
|--------|-------------|----------|
| U.S. State Dept | None | advisory_level |
| Open-Meteo | None | storm, flood |
| GDELT | None | civil_unrest |
| Amadeus GeoSure | `AMADEUS_CLIENT_ID` + `AMADEUS_CLIENT_SECRET` | physical_safety, health_medical, political_freedom, theft_risk |
| ACLED | `ACLED_API_KEY` + `ACLED_EMAIL` | conflict |

### Testing Requirements
- Test locally with `uv run uvicorn` before any Docker build
- Validate Docker container before pushing: `docker build && docker run`
- CI/CD: Cloud Build Trigger on push to `main`

## Dependencies

### External
- GCP Cloud Run — runtime
- GCP Firestore — response caching
- GCP BigQuery — event logging
- GCP Secret Manager — credentials at runtime
- GCP Artifact Registry — container images

<!-- MANUAL: -->
