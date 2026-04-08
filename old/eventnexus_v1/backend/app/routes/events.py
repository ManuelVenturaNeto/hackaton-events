"""Event API routes for listing, detail, populate, refresh, and sync."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import db
from app.models.event import EventResponse, PopulateSummary, RefreshSummary
from app.repositories.event_repository import EventRepository
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events")


def _get_discovery_service() -> DiscoveryService:
    """Create a DiscoveryService instance.

    Returns:
        DiscoveryService connected to the global database.
    """
    return DiscoveryService(db)


def _get_event_repo() -> EventRepository:
    """Create an EventRepository instance.

    Returns:
        EventRepository connected to the global database.
    """
    return EventRepository(db)


@router.get("", response_model=list[EventResponse])
def list_events(
    search: str = Query("", description="Free-text search"),
    category: str = Query("", description="Filter by category"),
    continent: str = Query("", description="Filter by continent"),
    country: str = Query("", description="Filter by country"),
    stateProvince: str = Query("", description="Filter by state/province"),
    city: str = Query("", description="Filter by city"),
    status: str = Query("", description="Filter by status"),
    format: str = Query("", description="Filter by format"),
    organizer: str = Query("", description="Filter by organizer"),
    company: str = Query("", description="Filter by company"),
    startDateFrom: str = Query("", description="Min start date"),
    startDateTo: str = Query("", description="Max start date"),
    endDateFrom: str = Query("", description="Min end date"),
    endDateTo: str = Query("", description="Max end date"),
    minAudienceSize: Optional[int] = Query(None, description="Min audience size"),
    maxAudienceSize: Optional[int] = Query(None, description="Max audience size"),
    sortBy: str = Query("networkingRelevance", description="Sort field"),
    sortOrder: str = Query("desc", description="Sort order"),
) -> list[EventResponse]:
    """List events with filters and sorting.

    Supports the full set of filters used by the frontend.

    Returns:
        List of events matching the filters.
    """
    repo = _get_event_repo()
    events = repo.list_events(
        search=search,
        category=category,
        continent=continent,
        country=country,
        state_province=stateProvince,
        city=city,
        status=status,
        format_=format,
        organizer=organizer,
        company=company,
        start_date_from=startDateFrom,
        start_date_to=startDateTo,
        end_date_from=endDateFrom,
        end_date_to=endDateTo,
        min_audience_size=minAudienceSize,
        max_audience_size=maxAudienceSize,
        sort_by=sortBy,
        sort_order=sortOrder,
    )
    logger.info("Listed %d events (search=%s, category=%s, country=%s)",
                len(events), search, category, country)
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str) -> EventResponse:
    """Get a single event by ID.

    Args:
        event_id: The event ID.

    Returns:
        Full event details.

    Raises:
        HTTPException: 404 if event not found.
    """
    repo = _get_event_repo()
    event = repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/populate", response_model=PopulateSummary)
def populate_events() -> PopulateSummary:
    """Discover and persist new events from all sources.

    Triggers the full discovery pipeline:
    1. Fetch from curated source (pre-researched real events)
    2. Fetch from web search source (concurrent HTTP scraping)
    3. Normalize and score each event
    4. Upsert into SQLite with deduplication

    Returns:
        Summary of the populate operation.
    """
    service = _get_discovery_service()
    return service.populate()


@router.post("/refresh-status", response_model=RefreshSummary)
def refresh_event_status() -> RefreshSummary:
    """Check existing events for status changes.

    Iterates through stored events and checks their official pages
    for cancellation or postponement signals using concurrent HTTP requests.

    Returns:
        Summary of status changes detected.
    """
    service = _get_discovery_service()
    return service.refresh_status()


@router.post("/sync")
def sync_events() -> dict:
    """Run full sync: populate + refresh-status.

    Combined orchestration endpoint that runs discovery
    followed by status refresh.

    Returns:
        Combined results from both operations.
    """
    service = _get_discovery_service()
    return service.sync()
