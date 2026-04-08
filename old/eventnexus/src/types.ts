export type EventStatus = 'upcoming' | 'canceled' | 'postponed' | 'completed';
export type EventFormat = 'in-person' | 'hybrid' | 'online';
export type EventCategory = 'Technology' | 'Banking / Financial' | 'Agribusiness / Agriculture' | 'Medical / Healthcare' | 'Business / Entrepreneurship';

export interface EventLocation {
  venueName?: string;
  streetAddress?: string;
  city: string;
  state?: string;
  country: string;
  postalCode?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export interface Company {
  name: string;
  role: 'organizer' | 'sponsor' | 'exhibitor' | 'partner' | 'featured';
}

export interface Event {
  id: string;
  name: string;
  location: EventLocation;
  startDate: string;
  endDate: string;
  duration: string;
  organizer: string;
  category: EventCategory;
  format: EventFormat;
  companies: Company[];
  audienceSize?: number;
  status: EventStatus;
  websiteUrl: string;
  description: string;
  networkingScore: number;
  lastUpdated: string;
  sourceUrl: string;
  confidence: number; // 0 to 1
}

export interface SearchFilters {
  category?: EventCategory;
  country?: string;
  city?: string;
  dateRange?: { start: string; end: string };
  status?: EventStatus;
  organizer?: string;
  company?: string;
  minAudience?: number;
  minNetworkingScore?: number;
  format?: EventFormat;
}

export type SortOption = 'soonest' | 'largest-audience' | 'highest-score' | 'most-companies' | 'recently-updated';
