export interface Location {
  venueName: string;
  fullStreetAddress: string;
  city: string;
  stateProvince: string;
  country: string;
  postalCode?: string;
}

export interface Company {
  name: string;
  role: 'organizer' | 'sponsor' | 'exhibitor' | 'partner' | 'featured';
}

export interface Event {
  id: string;
  name: string;
  location: Location;
  startDate: string;
  endDate: string;
  durationDays: number;
  organizer: string;
  category: 'Technology' | 'Banking / Financial' | 'Agribusiness / Agriculture' | 'Medical / Healthcare' | 'Business / Entrepreneurship';
  format: 'in-person' | 'hybrid' | 'online';
  companiesInvolved: Company[];
  expectedAudienceSize: number;
  status: 'upcoming' | 'canceled' | 'postponed' | 'completed';
  officialWebsiteUrl: string;
  briefDescription: string;
  networkingRelevanceScore: number;
  lastUpdated: string;
}
