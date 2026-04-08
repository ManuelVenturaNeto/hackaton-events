"""Service orchestrating event discovery from multiple sources."""

import logging
from datetime import date

from app.database import Database
from app.models.event import EventCreate
from app.repositories.event_repository import EventRepository
from app.repositories.sync_run_repository import SyncRunRepository
from app.services.normalization_service import NormalizationService
from app.services.scoring_service import ScoringService
from app.sources.curated_source import CuratedEventSource
# from app.sources.eventbrite_source import EventbriteSource
# from app.sources.sympla_scraper import SymplaScraperSource
# from app.sources.ticketmaster_source import TicketmasterSource
# from app.sources.web_search_source import WebSearchSource

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Orchestrates the full event discovery pipeline."""

    def __init__(self, database: Database) -> None:
        self.event_repo = EventRepository(database)
        self.sync_repo = SyncRunRepository(database)
        self.normalizer = NormalizationService()
        self.scorer = ScoringService()
        self.sources = [
            CuratedEventSource(),
            # TicketmasterSource(),
            # EventbriteSource(),
            # SymplaScraperSource(),
            # WebSearchSource(),
        ]

    def sync(self) -> dict:
        """Run full sync: fetch from all sources, normalize, score, persist."""
        run_id = self.sync_repo.start_run("sync")
        errors: list[str] = []
        all_events: list[EventCreate] = []

        for source in self.sources:
            try:
                events = source.fetch_events()
                all_events.extend(events)
                logger.info("Source '%s': %d events", source.name, len(events))
            except Exception as exc:
                error_msg = f"Source '{source.name}' failed: {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        today = date.today().isoformat()
        all_events = [
            e for e in all_events
            if not e.end_date or e.end_date >= today
        ]

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
                error_msg = f"Failed to persist '{event.name}': {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        status = "completed" if not errors else "completed_with_errors"
        self.sync_repo.complete_run(
            run_id,
            status=status,
            events_discovered=len(all_events),
            events_inserted=inserted,
            events_updated=updated,
            errors=errors,
        )

        return {
            "status": status,
            "runId": run_id,
            "eventsDiscovered": len(all_events),
            "eventsInserted": inserted,
            "eventsUpdated": updated,
            "errors": errors,
            "message": f"Discovered {len(all_events)} events. Inserted {inserted}, updated {updated}.",
        }
