"""Service orchestrating event discovery from multiple sources.

Discovery flow:
1. Fetch events from all registered sources concurrently
2. Normalize each event
3. Calculate networking relevance score
4. Persist via upsert (handles deduplication)
5. Track sync run metrics

Sources searched:
- CuratedEventSource: Pre-researched real events from official websites
- WebSearchSource: Dynamic web scraping of event aggregator sites

Global vs Brazil strategy:
- Global: Both sources contribute international events
- Brazil: Curated source has deliberately deeper Brazil coverage;
  Web search includes Brazil-specific category URLs

Daily refresh workflow:
- POST /api/events/populate triggers full discovery
- POST /api/events/refresh-status checks existing event status
- POST /api/events/sync runs both operations sequentially

Concurrency strategy:
- WebSearchSource uses ThreadPoolExecutor for parallel HTTP fetches
- Source-level fetching is sequential (curated + web_search)
- Individual URL fetches within web_search are concurrent
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from app.database import Database
from app.models.event import EventCreate, PopulateSummary, RefreshSummary
from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository
from app.services.normalization_service import NormalizationService
from app.services.scoring_service import ScoringService
from app.sources.curated_source import CuratedEventSource
from app.sources.web_search_source import WebSearchSource
from app.config import settings

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Orchestrates the full event discovery pipeline.

    Coordinates source fetching, normalization, scoring, and persistence.
    Tracks operation metrics via sync runs.
    """

    def __init__(self, database: Database) -> None:
        """Initialize with all required dependencies.

        Args:
            database: Database instance for persistence.
        """
        self.event_repo = EventRepository(database)
        self.sync_repo = SyncRunRepository(database)
        self.normalizer = NormalizationService()
        self.scorer = ScoringService()
        self.curated_source = CuratedEventSource()
        self.web_source = WebSearchSource()

    def populate(self) -> PopulateSummary:
        """Run full event discovery and populate the database.

        Fetches from all sources, normalizes, scores, and persists.
        Handles deduplication at the repository level.

        Returns:
            PopulateSummary with operation metrics.
        """
        run_id = self.sync_repo.start_run("populate")
        errors: list[str] = []
        all_events: list[EventCreate] = []

        # Fetch from curated source
        try:
            curated = self.curated_source.fetch_events()
            all_events.extend(curated)
            logger.info("Curated source: %d events", len(curated))
        except Exception as exc:
            error_msg = f"Curated source failed: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Fetch from web search source (uses internal concurrency)
        try:
            web_events = self.web_source.fetch_events()
            all_events.extend(web_events)
            logger.info("Web search source: %d events", len(web_events))
        except Exception as exc:
            error_msg = f"Web search source failed: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Filter out events that have already ended
        today = date.today().isoformat()
        all_events = [
            e for e in all_events
            if not e.end_date or e.end_date >= today
        ]

        # Process and persist
        inserted = 0
        updated = 0
        for event in all_events:
            try:
                normalized = self.normalizer.normalize(event)
                normalized.networking_relevance_score = self.scorer.calculate_score(normalized)
                _, was_new = self.event_repo.upsert_event(normalized)
                if was_new:
                    inserted += 1
                else:
                    updated += 1
            except Exception as exc:
                error_msg = f"Failed to persist event '{event.name}': {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        self.sync_repo.complete_run(
            run_id,
            status="completed" if not errors else "completed_with_errors",
            events_discovered=len(all_events),
            events_inserted=inserted,
            events_updated=updated,
            errors=errors,
        )

        summary = PopulateSummary(
            status="success" if not errors else "partial_success",
            events_discovered=len(all_events),
            events_inserted=inserted,
            events_updated=updated,
            events_deduplicated=updated,
            errors=errors,
            message=f"Discovered {len(all_events)} events. Inserted {inserted}, updated {updated}.",
        )
        logger.info("Populate completed: %s", summary.message)
        return summary

    def refresh_status(self) -> RefreshSummary:
        """Check existing events for status changes.

        Fetches each event's official page and looks for
        cancellation/postponement indicators. Uses ThreadPoolExecutor
        for concurrent checking.

        Returns:
            RefreshSummary with operation metrics.
        """
        run_id = self.sync_repo.start_run("refresh")
        events = self.event_repo.get_all_event_ids_and_urls()
        status_changes: list[dict] = []
        checked = 0

        def check_single(event_info: dict) -> dict | None:
            """Check a single event for status change."""
            url = event_info.get("official_website_url", "")
            name = event_info.get("name", "")
            current = event_info.get("status", "")

            # First check curated source
            new_status = self.curated_source.check_event_status(name, url)
            if not new_status and url:
                new_status = self.web_source.check_event_status(name, url)

            if new_status and new_status != current:
                return {
                    "event_id": event_info["id"],
                    "event_name": name,
                    "old_status": current,
                    "new_status": new_status,
                }
            return None

        with ThreadPoolExecutor(max_workers=settings.max_concurrent_fetches) as executor:
            futures = {
                executor.submit(check_single, ev): ev for ev in events
            }
            for future in as_completed(futures):
                checked += 1
                try:
                    result = future.result()
                    if result:
                        self.event_repo.update_status(result["event_id"], result["new_status"])
                        status_changes.append(result)
                        logger.info("Status change: %s %s -> %s",
                                    result["event_name"], result["old_status"], result["new_status"])
                except Exception as exc:
                    logger.warning("Error checking event status: %s", exc)

        self.sync_repo.complete_run(
            run_id,
            status="completed",
            events_discovered=checked,
            events_updated=len(status_changes),
        )

        summary = RefreshSummary(
            status="success",
            events_checked=checked,
            events_updated=len(status_changes),
            status_changes=status_changes,
            message=f"Checked {checked} events. {len(status_changes)} status changes detected.",
        )
        logger.info("Refresh completed: %s", summary.message)
        return summary

    def sync(self) -> dict:
        """Run both populate and refresh-status sequentially.

        Returns:
            Combined results dict.
        """
        populate_result = self.populate()
        refresh_result = self.refresh_status()
        return {
            "status": "success",
            "populate": populate_result.model_dump(),
            "refresh": refresh_result.model_dump(),
            "message": "Full sync completed.",
        }
