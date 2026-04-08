# EventNexus API — Design Spec

## Overview

API de mapeamento de eventos para o mercado brasileiro de viagens corporativas. O viajante corporativo busca eventos relevantes ao seu negócio (ex: devs viajando para Campus Party em SP) e precisa planejar a viagem com antecedência.

A API retorna eventos dos próximos 6 meses (parametrizável), com nome, data, localização e link para compra de ingresso.

**Stack:** Python + FastAPI, rodando em Cloud Run, com Supabase (PostgreSQL) como banco de dados.

**Escopo:** Backend only. O frontend antigo (`old/eventnexus/`) serve como referência para o contrato de dados.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Cloud Run                         │
│  ┌───────────────────────────────────────────────┐  │
│  │              FastAPI Application               │  │
│  │                                                │  │
│  │  Routes ──► Services ──► Repositories ──► DB   │  │
│  │                │                               │  │
│  │           Sources (5)                          │  │
│  │  ┌──────────┬──────────┬────────────────────┐  │  │
│  │  │ Curated  │  APIs    │   Web Scrapers     │  │  │
│  │  │ (35 evts)│ Ticket-  │  Sympla            │  │  │
│  │  │          │ master   │  10times.com       │  │  │
│  │  │          │ Event-   │  confs.tech        │  │  │
│  │  │          │ brite    │                    │  │  │
│  │  └──────────┴──────────┴────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                        │                             │
│                        ▼                             │
│              Supabase (PostgreSQL)                   │
└─────────────────────────────────────────────────────┘
         ▲
         │  Cloud Scheduler (cron diário)
         │  POST /api/events/sync
```

**Abordagem:** Migração direta do código antigo (`old/eventnexus_v1/backend/`). Reutiliza a arquitetura sources → services → repositories → routes, substituindo SQLite por Supabase/PostgreSQL e adicionando novas fontes de dados.

O sync usa `BackgroundTasks` do FastAPI (nativo) para evitar timeout na Cloud Run.

---

## Modelo de Dados (Supabase/PostgreSQL)

### events

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK DEFAULT gen_random_uuid() | |
| name | VARCHAR(500) NOT NULL | |
| organizer | VARCHAR(300) | |
| category | VARCHAR(50) | Technology, Banking/Financial, Agribusiness/Agriculture, Medical/Healthcare, Business/Entrepreneurship |
| format | VARCHAR(20) | in-person, hybrid, online |
| status | VARCHAR(20) DEFAULT 'upcoming' | upcoming, canceled, postponed, completed |
| expected_audience_size | INTEGER | |
| official_website_url | TEXT | |
| brief_description | TEXT | |
| networking_relevance_score | FLOAT DEFAULT 0 | 0-100 |
| start_date | DATE | |
| end_date | DATE | |
| duration_days | INTEGER DEFAULT 1 | |
| dedup_key | VARCHAR(500) UNIQUE NOT NULL | chave composta normalizada |
| created_at | TIMESTAMPTZ DEFAULT now() | |
| last_updated | TIMESTAMPTZ DEFAULT now() | |

### event_locations (1:1 com events)

| Coluna | Tipo |
|--------|------|
| id | UUID PK |
| event_id | UUID FK → events (UNIQUE, ON DELETE CASCADE) |
| venue_name | VARCHAR(300) |
| full_street_address | TEXT |
| city | VARCHAR(200) |
| state_province | VARCHAR(200) |
| country | VARCHAR(100) |
| postal_code | VARCHAR(20) |
| continent | VARCHAR(50) |
| neighborhood | VARCHAR(200) |
| street | VARCHAR(300) |
| street_number | VARCHAR(50) |
| latitude | DOUBLE PRECISION |
| longitude | DOUBLE PRECISION |

### event_companies (N:1 com events)

| Coluna | Tipo |
|--------|------|
| id | UUID PK |
| event_id | UUID FK → events (ON DELETE CASCADE) |
| name | VARCHAR(300) NOT NULL |
| role | VARCHAR(50) NOT NULL — organizer, sponsor, exhibitor, partner, featured |

### event_sources (N:1 com events)

| Coluna | Tipo |
|--------|------|
| id | UUID PK |
| event_id | UUID FK → events (ON DELETE CASCADE) |
| source_name | VARCHAR(100) |
| source_url | TEXT |
| confidence | FLOAT (0.0-1.0) |
| fetched_at | TIMESTAMPTZ DEFAULT now() |

### sync_runs (log operacional)

| Coluna | Tipo |
|--------|------|
| id | UUID PK |
| run_type | VARCHAR(20) — populate, refresh, sync |
| started_at | TIMESTAMPTZ DEFAULT now() |
| completed_at | TIMESTAMPTZ |
| status | VARCHAR(30) — running, completed, completed_with_errors, failed |
| events_discovered | INTEGER DEFAULT 0 |
| events_inserted | INTEGER DEFAULT 0 |
| events_updated | INTEGER DEFAULT 0 |
| errors | JSONB DEFAULT '[]' |

### Indexes

- events: category, status, start_date, networking_relevance_score DESC, dedup_key (unique)
- event_locations: country, city
- event_companies: event_id
- event_sources: event_id

---

## Fontes de Dados

### 1. Curated Source (confiança: 0.95)

Lista hardcoded de ~35 eventos reais pesquisados manualmente (AWS re:Invent, Campus Party, FEBRABAN TECH, Web Summit Rio, etc.). Serve como fallback — garante dados mínimos mesmo se APIs/scraping falharem.

### 2. Ticketmaster Discovery API (confiança: 0.80)

- **Endpoint:** `GET /discovery/v2/events.json`
- **Cadastro:** Gratuito em developer.ticketmaster.com
- **Limite:** 5 req/s, 5.000/dia
- **Parâmetros:** keyword, countryCode=BR, classificationName, startDateTime, endDateTime, size=200
- **Dados:** nome, datas, venue (com lat/lng), URL de compra, classificações

### 3. Eventbrite API (confiança: 0.80)

- **Endpoint:** `GET /v3/events/search/`
- **Cadastro:** Gratuito (tier básico)
- **Limite:** 2.000 req/hora
- **Parâmetros:** location.address=Brazil, categories, start_date.range_start/end, expand=venue,organizer
- **Dados:** nome, descrição, datas, venue, organizador, URL, capacidade

### 4. Sympla Web Scraper (confiança: 0.50)

- Scraping das páginas de listagem da Sympla por categoria + localização
- BeautifulSoup + httpx
- Dados: nome, data, local, URL do evento

### 5. Web Scraper Genérico (confiança: 0.50)

- Alvos: 10times.com (Brasil por categoria), confs.tech
- Mesma implementação do código antigo com ThreadPoolExecutor
- Limite: 50 eventos por source URL

---

## Pipeline de Sync

```
POST /api/events/sync
│
├─ Retorna imediatamente: { "status": "sync_started", "runId": "..." }
│
└─ BackgroundTask:
   1. Buscar de todas as 5 fontes em paralelo (ThreadPoolExecutor)
   2. Filtrar eventos com end_date < hoje
   3. Para cada evento:
      a. Normalizar (país, continente, duração)
      b. Calcular networking_relevance_score (0-100)
      c. Upsert no Supabase (dedup por chave composta)
   4. Registrar sync_run com métricas
```

---

## Scoring — Networking Relevance (0-100)

| Componente | Pontos | Critério |
|------------|--------|----------|
| Audiência | 5-30 | 100k+ (30), 50k+ (27), 20k+ (24), 10k+ (20), 5k+ (15), 1k+ (10), <1k (5) |
| Empresas | 0-25 | 10+ (25), 5+ (20), 3+ (15), 1+ (10), 0 (0) |
| Categoria | 10-15 | Tech (15), Banking (13), Business (12), Medical (11), Agri (10) |
| Formato | 4-10 | Presencial (10), Híbrido (8), Online (4) |
| Duração | 3-10 | 4+ dias (10), 3 dias (8), 2 dias (6), 1 dia (3) |
| Bonus Brasil | 0-10 | country == "Brazil" → +10 |

Máximo: 100 (capped).

---

## Normalização

- Trim de whitespace em todos os campos texto
- Padronização de país via aliases ("brasil" → "Brazil", "united states" → "USA")
- Inferência de continente a partir do país
- Cálculo de duração se ausente (end_date - start_date + 1, mínimo 1)

---

## Deduplicação

Chave composta determinística:

```
lower(name) | lower(organizer) | start_date | lower(city) | lower(country) | lower(url.rstrip('/'))
```

- Case-insensitive, URL sem trailing slash
- Constraint UNIQUE na coluna dedup_key
- Upsert: se existe, atualiza; se não, insere
- Múltiplas sources podem referenciar o mesmo evento (registros aditivos)

---

## Endpoints

### GET /api/health

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-08T12:00:00Z"
}
```

### GET /api/events

**Query params:** search, category, format, status (default: upcoming), country, city, startDateFrom, startDateTo, minAudienceSize, sortBy (default: networkingRelevance), sortOrder (default: desc)

Sem paginação. Retorna array completo de Event objects.

```json
[
  {
    "id": "uuid",
    "name": "Campus Party Brasil 2026",
    "organizer": "Campus Party",
    "category": "Technology",
    "format": "in-person",
    "status": "upcoming",
    "expectedAudienceSize": 100000,
    "officialWebsiteUrl": "https://brasil.campus-party.org",
    "briefDescription": "...",
    "networkingRelevanceScore": 87.5,
    "startDate": "2026-07-15",
    "endDate": "2026-07-19",
    "durationDays": 5,
    "lastUpdated": "2026-04-08T12:00:00Z",
    "location": {
      "venueName": "Expo Center Norte",
      "fullStreetAddress": "Rua José Bernardo Pinto, 333",
      "city": "São Paulo",
      "stateProvince": "SP",
      "country": "Brazil",
      "postalCode": "02055-000",
      "continent": "South America",
      "latitude": -23.5155,
      "longitude": -46.6264
    },
    "companiesInvolved": [
      { "name": "Campus Party", "role": "organizer" },
      { "name": "Lenovo", "role": "sponsor" }
    ],
    "sources": [
      { "sourceName": "curated", "confidence": 0.95 }
    ]
  }
]
```

### GET /api/events/{event_id}

Mesmo objeto Event acima, singular. 404 se não encontrado.

### POST /api/events/sync

Dispara sync em background. Resposta imediata:

```json
{
  "status": "sync_started",
  "runId": "uuid",
  "message": "Synchronization started in background"
}
```

---

## Estrutura do Projeto

```
/home/robson/code/hackaton/eventnexus/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + lifespan
│   ├── config.py                   # Settings (pydantic-settings)
│   ├── database.py                 # Conexão PostgreSQL (Supabase)
│   ├── models/
│   │   └── event.py                # Pydantic schemas + enums
│   ├── repositories/
│   │   ├── event_repository.py     # CRUD + upsert + dedup
│   │   └── sync_run_repository.py
│   ├── services/
│   │   ├── discovery_service.py    # Orquestra sync
│   │   ├── normalization_service.py
│   │   └── scoring_service.py
│   ├── sources/
│   │   ├── base_source.py          # Interface abstrata
│   │   ├── curated_source.py       # ~35 eventos hardcoded
│   │   ├── ticketmaster_source.py  # Discovery API
│   │   ├── eventbrite_source.py    # Search API
│   │   ├── sympla_scraper.py       # Web scraping
│   │   └── web_search_source.py    # 10times + confs.tech
│   └── routes/
│       ├── health.py
│       └── events.py
├── migrations/
│   ├── 001_create_tables.sql
│   └── 002_create_indexes.sql
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Migrations (Supabase)

### 001_create_tables.sql

```sql
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
```

### 002_create_indexes.sql

```sql
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_score ON events(networking_relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_locations_country ON event_locations(country);
CREATE INDEX IF NOT EXISTS idx_locations_city ON event_locations(city);
CREATE INDEX IF NOT EXISTS idx_companies_event ON event_companies(event_id);
CREATE INDEX IF NOT EXISTS idx_sources_event ON event_sources(event_id);
```

Migrations rodam automaticamente no startup (lifespan do FastAPI) e são idempotentes. Também podem ser executadas manualmente via SQL Editor do Supabase.

---

## Execução Local

### Opção 1 — Docker Compose (recomendado)

```bash
cd eventnexus
cp .env.example .env   # preencher API keys
docker-compose up
```

Sobe PostgreSQL 16 (porta 5432) + FastAPI (porta 8000) com hot reload.

### Opção 2 — Direto contra Supabase

```bash
cd eventnexus
cp .env.example .env   # preencher DATABASE_URL do Supabase + API keys
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Variáveis de ambiente (.env.example)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eventnexus

# Para Supabase (produção)
# DATABASE_URL=postgresql://postgres.prvljsmnyxvvgzmvsgzz:[PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# API Keys
TICKETMASTER_API_KEY=
EVENTBRITE_API_TOKEN=

# App
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
MAX_CONCURRENT_FETCHES=10
REQUEST_TIMEOUT_SECONDS=30
```

---

## Deploy (Cloud Run)

- Dockerfile com `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- DATABASE_URL do Supabase como secret no Cloud Run
- Cloud Scheduler job diário (ex: 03:00 BRT) faz `POST /api/events/sync`

---

## Autenticação

API aberta (sem auth) nesta versão. Futuramente: OAuth para busca autenticada (fora do escopo deste plano).

---

## Decisões & Trade-offs

1. **Migração direta vs reescrita:** Reutilizamos a arquitetura do código antigo por velocidade (hackathon). ThreadPoolExecutor síncrono em vez de async puro.
2. **BackgroundTasks vs Celery:** BackgroundTasks nativo do FastAPI — sem infra extra (Redis/worker). Suficiente para o volume esperado.
3. **Sympla como scraper:** API oficial só retorna eventos do próprio organizador. Scraping necessário para busca geral.
4. **Sem paginação:** Conforme requisito. Volume esperado de eventos nos próximos 6 meses é gerenciável sem paginação.
5. **Migrations no startup:** Idempotentes com IF NOT EXISTS. Simples para hackathon, sem necessidade de Alembic.
