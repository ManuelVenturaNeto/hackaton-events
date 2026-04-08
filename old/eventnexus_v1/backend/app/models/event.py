"""Pydantic models for events, matching the frontend contract."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    """Supported event categories."""

    TECHNOLOGY = "Technology"
    BANKING_FINANCIAL = "Banking / Financial"
    AGRIBUSINESS = "Agribusiness / Agriculture"
    MEDICAL = "Medical / Healthcare"
    BUSINESS = "Business / Entrepreneurship"


class EventFormat(str, Enum):
    """Supported event formats."""

    IN_PERSON = "in-person"
    HYBRID = "hybrid"
    ONLINE = "online"


class EventStatus(str, Enum):
    """Supported event statuses."""

    UPCOMING = "upcoming"
    CANCELED = "canceled"
    POSTPONED = "postponed"
    COMPLETED = "completed"


class CompanyRole(str, Enum):
    """Roles a company can have in an event."""

    ORGANIZER = "organizer"
    SPONSOR = "sponsor"
    EXHIBITOR = "exhibitor"
    PARTNER = "partner"
    FEATURED = "featured"


class LocationModel(BaseModel):
    """Location details for an event, matching frontend Location interface."""

    venue_name: str = ""
    full_street_address: str = ""
    city: str = ""
    state_province: str = ""
    country: str = ""
    postal_code: str = ""
    continent: str = ""
    neighborhood: str = ""
    street: str = ""
    street_number: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompanyModel(BaseModel):
    """Company involved in an event, matching frontend Company interface."""

    name: str
    role: CompanyRole


class EventCreate(BaseModel):
    """Model for creating a new event internally."""

    name: str
    organizer: str
    category: EventCategory
    format: EventFormat
    status: EventStatus = EventStatus.UPCOMING
    expected_audience_size: int = 0
    official_website_url: str = ""
    brief_description: str = ""
    networking_relevance_score: float = 0.0
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    location: LocationModel = Field(default_factory=LocationModel)
    companies: list[CompanyModel] = Field(default_factory=list)
    source_url: str = ""
    source_name: str = ""
    source_confidence: float = 1.0


class EventResponse(BaseModel):
    """Event response model matching the frontend Event interface exactly."""

    id: str
    name: str
    location: dict
    startDate: str
    endDate: str
    durationDays: int
    organizer: str
    category: str
    format: str
    companiesInvolved: list[dict]
    expectedAudienceSize: int
    status: str
    officialWebsiteUrl: str
    briefDescription: str
    networkingRelevanceScore: float
    lastUpdated: str


class PopulateSummary(BaseModel):
    """Summary of a populate operation."""

    status: str
    events_discovered: int = 0
    events_inserted: int = 0
    events_updated: int = 0
    events_deduplicated: int = 0
    errors: list[str] = Field(default_factory=list)
    message: str = ""


class RefreshSummary(BaseModel):
    """Summary of a refresh-status operation."""

    status: str
    events_checked: int = 0
    events_updated: int = 0
    status_changes: list[dict] = Field(default_factory=list)
    message: str = ""
