CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    organizer VARCHAR(300),
    category VARCHAR(50),
    format VARCHAR(20),
    status VARCHAR(20) DEFAULT 'upcoming',
    expected_audience_size INTEGER,
    official_website_url TEXT,
    brief_description TEXT,
    networking_relevance_score FLOAT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    duration_days INTEGER DEFAULT 1,
    dedup_key VARCHAR(500) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    venue_name VARCHAR(300),
    full_street_address TEXT,
    city VARCHAR(200),
    state_province VARCHAR(200),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    continent VARCHAR(50),
    neighborhood VARCHAR(200),
    street VARCHAR(300),
    street_number VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS event_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    role VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS event_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    source_name VARCHAR(100),
    source_url TEXT,
    confidence FLOAT DEFAULT 0,
    fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(30) DEFAULT 'running',
    events_discovered INTEGER DEFAULT 0,
    events_inserted INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb
);
