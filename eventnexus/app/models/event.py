"""Pydantic models for events, matching the frontend contract."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    TECHNOLOGY = "Technology"
    BANKING_FINANCIAL = "Banking / Financial"
    AGRIBUSINESS = "Agribusiness / Agriculture"
    MEDICAL = "Medical / Healthcare"
    BUSINESS = "Business / Entrepreneurship"


class EventFormat(str, Enum):
    IN_PERSON = "in-person"
    HYBRID = "hybrid"
    ONLINE = "online"


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    CANCELED = "canceled"
    POSTPONED = "postponed"
    COMPLETED = "completed"


class CompanyRole(str, Enum):
    ORGANIZER = "organizer"
    SPONSOR = "sponsor"
    EXHIBITOR = "exhibitor"
    PARTNER = "partner"
    FEATURED = "featured"


class LocationModel(BaseModel):
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
    name: str
    role: CompanyRole


class SourceModel(BaseModel):
    source_name: str = Field(alias="sourceName", default="")
    confidence: float = 0.0

    model_config = {"populate_by_name": True}


class EventCreate(BaseModel):
    """Internal model for creating/updating events."""
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


class LocationResponse(BaseModel):
    """Location in camelCase for frontend."""
    venueName: str = ""
    fullStreetAddress: str = ""
    city: str = ""
    stateProvince: str = ""
    country: str = ""
    postalCode: str = ""
    continent: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompanyResponse(BaseModel):
    name: str
    role: str


class SourceResponse(BaseModel):
    sourceName: str = ""
    confidence: float = 0.0


class EventResponse(BaseModel):
    """Event response matching the frontend contract (camelCase)."""
    id: str
    name: str
    organizer: str
    category: str
    format: str
    status: str
    expectedAudienceSize: int
    officialWebsiteUrl: str
    briefDescription: str
    networkingRelevanceScore: float
    startDate: str
    endDate: str
    durationDays: int
    lastUpdated: str
    location: LocationResponse
    companiesInvolved: list[CompanyResponse]
    sources: list[SourceResponse] = Field(default_factory=list)


class SyncStartResponse(BaseModel):
    """Response for POST /api/events/sync."""
    status: str
    runId: str
    message: str
