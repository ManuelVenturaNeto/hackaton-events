import type { Event, SearchFilters, SyncResponse } from './types';

let _cache: Event[] | null = null;

async function loadEvents(): Promise<Event[]> {
  if (_cache) return _cache;
  const response = await fetch('/events.json');
  if (!response.ok) throw new Error('Falha ao carregar eventos');
  const raw: any[] = await response.json();

  _cache = raw.map((e, i) => ({
    id: e.id || String(i),
    name: e.name || '',
    organizer: e.organizer || '',
    category: e.category || 'Technology',
    format: e.format || 'in-person',
    status: e.status || 'upcoming',
    expectedAudienceSize: e.expected_audience_size || 0,
    officialWebsiteUrl: e.official_website_url || '',
    briefDescription: e.brief_description || '',
    networkingRelevanceScore: e.networking_relevance_score || 0,
    startDate: e.start_date || '',
    endDate: e.end_date || '',
    durationDays: e.duration_days || 1,
    lastUpdated: '',
    location: {
      venueName: e.location?.venue_name || '',
      fullStreetAddress: e.location?.full_street_address || '',
      city: e.location?.city || '',
      stateProvince: e.location?.state_province || '',
      country: e.location?.country || '',
      postalCode: e.location?.postal_code || '',
      continent: e.location?.continent || '',
      latitude: e.location?.latitude || null,
      longitude: e.location?.longitude || null,
    },
    companiesInvolved: (e.companies || []).map((c: any) => ({
      name: c.name || '',
      role: c.role || 'partner',
    })),
    sources: [{ sourceName: 'curated', confidence: e.source_confidence || 0.95 }],
  }));

  return _cache;
}

export async function fetchEvents(filters: SearchFilters = {}): Promise<Event[]> {
  let events = await loadEvents();

  // Filter
  if (filters.search) {
    const q = filters.search.toLowerCase();
    events = events.filter(e =>
      e.name.toLowerCase().includes(q) ||
      e.organizer.toLowerCase().includes(q) ||
      e.briefDescription.toLowerCase().includes(q)
    );
  }
  if (filters.category) {
    events = events.filter(e => e.category.toLowerCase() === filters.category!.toLowerCase());
  }
  if (filters.country) {
    events = events.filter(e => e.location.country.toLowerCase() === filters.country!.toLowerCase());
  }
  if (filters.city) {
    events = events.filter(e => e.location.city.toLowerCase() === filters.city!.toLowerCase());
  }
  if (filters.format) {
    events = events.filter(e => e.format.toLowerCase() === filters.format!.toLowerCase());
  }
  if (filters.dateRange) {
    const today = new Date().toISOString().slice(0, 10);
    const end = new Date(Date.now() + Number(filters.dateRange) * 86400000).toISOString().slice(0, 10);
    events = events.filter(e => e.startDate >= today && e.startDate <= end);
  }

  // Default: only upcoming, exclude past
  const today = new Date().toISOString().slice(0, 10);
  events = events.filter(e => !e.endDate || e.endDate >= today);
  events = events.filter(e => e.status === 'upcoming');

  return events;
}

export async function fetchEventById(id: string): Promise<Event> {
  const events = await loadEvents();
  const event = events.find(e => e.id === id);
  if (!event) throw new Error('Evento não encontrado');
  return event;
}

export async function triggerSync(): Promise<SyncResponse> {
  return { status: 'ok', runId: 'local', message: 'Dados carregados do JSON estático' };
}

export async function fetchFlightUrl(eventId: string, origin: string = 'belo horizonte'): Promise<{ url: string | null; error: string | null }> {
  return { url: null, error: 'Serviço de voos indisponível no modo estático' };
}

export async function fetchHotelUrl(eventId: string): Promise<{ url: string | null; error: string | null }> {
  return { url: null, error: 'Serviço de hotéis indisponível no modo estático' };
}

export async function checkHealth(): Promise<{ status: string; database: string }> {
  return { status: 'healthy', database: 'json' };
}
