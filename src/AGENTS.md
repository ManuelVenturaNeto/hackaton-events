<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-08 | Updated: 2026-04-08 -->

# src

## Purpose
Active development directory for the hackathon. Contains the Duty of Care travel risk API specifications, implementation plans, and brand/visual identity assets. This is where all new features are designed and documented before implementation.

## Key Files

| File | Description |
|------|-------------|
| `Prompt.md` | Original hackathon brief — Event Mapper requirements, API endpoints, stack decisions, and Supabase connection strings |
| `visual-identity-report.md` | Brand guidelines and visual identity for the product |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `duty-of-care/` | Duty of Care travel risk API specs and plans (see `duty-of-care/AGENTS.md`) |
| `Referencias do site/` | Visual reference assets and screenshots |

## For AI Agents

### Working In This Directory
- `Prompt.md` is the canonical product brief — read it first when starting any implementation task
- The Supabase connection strings in `Prompt.md` use a placeholder `[YOUR-PASSWORD]`; never commit real credentials
- Implementation follows the reference code in `../old/eventnexus_v1/` — reuse patterns from there

### Common Patterns
- Specs go in `duty-of-care/specs/` as dated markdown files (format: `YYYY-MM-DD-<feature>.md`)
- Plans go in `duty-of-care/plans/` following the same naming convention

## Dependencies

### Internal
- `../old/eventnexus_v1/` — reference implementation for Event Mapper backend and frontend

### External
- Supabase PostgreSQL (pooler: `aws-1-sa-east-1.pooler.supabase.com:6543`)
- GCP Cloud Run deployment target

<!-- MANUAL: -->
