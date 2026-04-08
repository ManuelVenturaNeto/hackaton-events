export type EventStatus = 'upcoming' | 'canceled' | 'postponed' | 'completed';
export type EventFormat = 'in-person' | 'hybrid' | 'online';
export type EventCategory =
  | 'Technology'
  | 'Banking / Financial'
  | 'Agribusiness / Agriculture'
  | 'Medical / Healthcare'
  | 'Business / Entrepreneurship';

export interface EventLocation {
  venueName: string;
  fullStreetAddress: string;
  city: string;
  stateProvince: string;
  country: string;
  postalCode: string;
  continent: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Company {
  name: string;
  role: string;
}

export interface EventSource {
  sourceName: string;
  confidence: number;
}

export interface Event {
  id: string;
  name: string;
  organizer: string;
  category: string;
  format: string;
  status: string;
  expectedAudienceSize: number;
  officialWebsiteUrl: string;
  briefDescription: string;
  networkingRelevanceScore: number;
  startDate: string;
  endDate: string;
  durationDays: number;
  lastUpdated: string;
  location: EventLocation;
  companiesInvolved: Company[];
  sources: EventSource[];
}

export interface SearchFilters {
  category?: EventCategory;
  country?: string;
  city?: string;
  format?: EventFormat;
  dateRange?: string;
  search?: string;
}

export type SortOption =
  | 'highest-score'
  | 'soonest'
  | 'largest-audience'
  | 'most-companies'
  | 'recently-updated';

export interface LocationSuggestion {
  value: string;
  type: string;
  filterKey: 'city' | 'country';
  country?: string;
}

export interface SyncResponse {
  status: string;
  runId: string;
  message: string;
}
