import { Event, SearchFilters, Company } from "../types.ts";

export function processEvents(events: Event[], filters: SearchFilters): Event[] {
  // 1. Normalization
  let processed = events.map(event => normalizeEvent(event));

  // 2. Deduplication (Fuzzy matching simulation)
  processed = deduplicateEvents(processed);

  // 3. Scoring
  processed = processed.map(event => ({
    ...event,
    networkingScore: calculateNetworkingScore(event)
  }));

  // 4. Filtering
  if (filters.category) {
    processed = processed.filter(e => e.category === filters.category);
  }
  if (filters.country) {
    processed = processed.filter(e => e.location.country.toLowerCase().includes(filters.country!.toLowerCase()));
  }
  if (filters.city) {
    processed = processed.filter(e => e.location.city.toLowerCase().includes(filters.city!.toLowerCase()));
  }
  if (filters.status) {
    processed = processed.filter(e => e.status === filters.status);
  }
  if (filters.format) {
    processed = processed.filter(e => e.format === filters.format);
  }
  if (filters.minAudience) {
    processed = processed.filter(e => (e.audienceSize || 0) >= filters.minAudience!);
  }

  return processed;
}

function normalizeEvent(event: Event): Event {
  return {
    ...event,
    id: event.id || Math.random().toString(36).substr(2, 9),
    lastUpdated: new Date().toISOString(),
    duration: calculateDuration(event.startDate, event.endDate),
    confidence: 0.95 // High confidence for these sources
  };
}

function calculateDuration(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const diffTime = Math.abs(e.getTime() - s.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  return `${diffDays} days`;
}

function deduplicateEvents(events: Event[]): Event[] {
  const seen = new Map<string, Event>();
  
  events.forEach(event => {
    // Simple key for deduplication: Name + Date + City
    const key = `${event.name.toLowerCase()}-${event.startDate}-${event.location.city.toLowerCase()}`;
    if (!seen.has(key)) {
      seen.set(key, event);
    } else {
      // Merge logic (prefer official source if we had multiple)
      const existing = seen.get(key)!;
      seen.set(key, { ...existing, ...event });
    }
  });

  return Array.from(seen.values());
}

function calculateNetworkingScore(event: Event): number {
  let score = 0;

  // Audience size (max 40 points)
  if (event.audienceSize) {
    if (event.audienceSize > 50000) score += 40;
    else if (event.audienceSize > 10000) score += 30;
    else if (event.audienceSize > 5000) score += 20;
    else if (event.audienceSize > 1000) score += 10;
  }

  // Companies involved (max 30 points)
  const companyCount = event.companies.length;
  score += Math.min(companyCount * 5, 30);

  // Sector relevance (max 15 points)
  if (event.category === 'Technology') score += 15;
  else if (event.category === 'Banking / Financial') score += 10;
  else score += 5;

  // Format (max 15 points)
  if (event.format === 'in-person') score += 15;
  else if (event.format === 'hybrid') score += 10;
  else score += 5;

  return Math.min(score, 100);
}
