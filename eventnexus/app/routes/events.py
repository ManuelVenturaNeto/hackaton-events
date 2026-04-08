"""Event API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.database import db
from app.models.event import EventResponse, SyncStartResponse
from app.repositories.event_repository import EventRepository
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events")


def _get_repo() -> EventRepository:
    return EventRepository(db)


def _run_sync() -> None:
    """Background task: run full sync."""
    try:
        service = DiscoveryService(db)
        result = service.sync()
        logger.info("Background sync completed: %s", result["message"])
    except Exception as exc:
        logger.error("Background sync failed: %s", exc)


@router.get("", response_model=list[EventResponse])
def list_events(
    search: str = Query("", description="Free-text search"),
    category: str = Query("", description="Filter by category"),
    country: str = Query("", description="Filter by country"),
    city: str = Query("", description="Filter by city"),
    status: str = Query("", description="Filter by status"),
    format: str = Query("", description="Filter by format"),
    startDateFrom: str = Query("", description="Min start date"),
    startDateTo: str = Query("", description="Max start date"),
    minAudienceSize: Optional[int] = Query(None, description="Min audience"),
    sortBy: str = Query("networkingRelevance", description="Sort field"),
    sortOrder: str = Query("desc", description="Sort order"),
) -> list[EventResponse]:
    repo = _get_repo()
    return repo.list_events(
        search=search,
        category=category,
        country=country,
        city=city,
        status=status,
        format_=format,
        start_date_from=startDateFrom,
        start_date_to=startDateTo,
        min_audience_size=minAudienceSize,
        sort_by=sortBy,
        sort_order=sortOrder,
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str) -> EventResponse:
    repo = _get_repo()
    event = repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/flight-url")
def get_flight_url(
    event_id: str,
    origin: str = Query("belo horizonte", description="Cidade de origem"),
) -> dict:
    """Generate Onfly flight booking URL for an event."""
    repo = _get_repo()
    event = repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.services.flight_service import generate_flight_url_for_event
    result = generate_flight_url_for_event(
        event_city=event.location.city,
        event_start_date=event.startDate,
        event_end_date=event.endDate,
        origin_city=origin,
    )
    return result


@router.get("/{event_id}/hotel-url")
def get_hotel_url(event_id: str) -> dict:
    """Generate Onfly hotel booking URL for an event."""
    repo = _get_repo()
    event = repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.services.hotel_service import generate_hotel_url_for_event
    result = generate_hotel_url_for_event(
        event_city=event.location.city,
        event_start_date=event.startDate,
        event_end_date=event.endDate,
    )
    return result


@router.post("/sync", response_model=SyncStartResponse)
def sync_events(background_tasks: BackgroundTasks) -> SyncStartResponse:
    """Trigger event synchronization in background."""
    from app.repositories.sync_run_repository import SyncRunRepository
    sync_repo = SyncRunRepository(db)
    run_id = sync_repo.start_run("sync")

    background_tasks.add_task(_run_sync)

    return SyncStartResponse(
        status="sync_started",
        runId=run_id,
        message="Synchronization started in background",
    )
