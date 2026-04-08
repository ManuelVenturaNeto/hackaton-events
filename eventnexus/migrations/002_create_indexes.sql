CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_score ON events(networking_relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_locations_country ON event_locations(country);
CREATE INDEX IF NOT EXISTS idx_locations_city ON event_locations(city);
CREATE INDEX IF NOT EXISTS idx_companies_event ON event_companies(event_id);
CREATE INDEX IF NOT EXISTS idx_sources_event ON event_sources(event_id);
