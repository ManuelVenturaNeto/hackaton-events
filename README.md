# EventNexus — Mapeador de Eventos Corporativos

Plataforma de mapeamento de eventos para o mercado brasileiro de viagens corporativas. O viajante corporativo busca eventos relevantes ao seu negócio e planeja sua viagem com antecedência.

## Arquitetura

```
eventnexus/          # Backend (FastAPI + PostgreSQL/Supabase)
eventnexus-frontend/ # Frontend (React 19 + Vite + Tailwind)
```

### Backend (`eventnexus/`)

API REST que agrega eventos de 5 fontes:

| Fonte | Tipo | Confiança |
|-------|------|-----------|
| Lista Curada | ~35 eventos reais hardcoded | 0.95 |
| Ticketmaster | Discovery API | 0.80 |
| Eventbrite | Search API | 0.80 |
| Sympla | Web scraping | 0.50 |
| 10times / confs.tech | Web scraping | 0.50 |

**Endpoints:**

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/events` | Listar eventos (filtros, ordenacao) |
| GET | `/api/events/{id}` | Detalhe de um evento |
| POST | `/api/events/sync` | Disparar sincronizacao (background) |

**Stack:** Python 3.11+, FastAPI, psycopg2, httpx, BeautifulSoup4, pydantic-settings

### Frontend (`eventnexus-frontend/`)

SPA React consumindo a API do backend.

**Stack:** React 19, Vite 6, TypeScript, Tailwind CSS 4, Motion, Lucide React, date-fns

**Identidade Visual:** Baseada na marca Onfly — paleta de azuis, fonte Poppins, botoes pill (56px radius), cards com glassmorphism.

## Como Rodar

### Backend

**Opcao 1 — Docker Compose (recomendado):**

```bash
cd eventnexus
cp .env.example .env   # preencher API keys
docker compose up       # PostgreSQL 16 + FastAPI na porta 8000
```

**Opcao 2 — Local com Supabase:**

```bash
cd eventnexus
cp .env.example .env   # preencher DATABASE_URL do Supabase + API keys
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd eventnexus-frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm install
npm run dev            # Vite na porta 5173
```

### Primeiro Sync

Apos subir o backend, popular o banco:

```bash
curl -X POST http://localhost:8000/api/events/sync
```

## Variaveis de Ambiente

### Backend (`eventnexus/.env`)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eventnexus
TICKETMASTER_API_KEY=
EVENTBRITE_API_TOKEN=
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
MAX_CONCURRENT_FETCHES=10
REQUEST_TIMEOUT_SECONDS=30
```

### Frontend (`eventnexus-frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

## Scoring de Networking (0-100)

Cada evento recebe um score baseado em:

| Componente | Pontos | Criterio |
|------------|--------|----------|
| Audiencia | 5-30 | Tamanho do publico esperado |
| Empresas | 0-25 | Quantidade de empresas envolvidas |
| Categoria | 10-15 | Tech > Banking > Business > Medical > Agri |
| Formato | 4-10 | Presencial > Hibrido > Online |
| Duracao | 3-10 | Mais dias = mais networking |
| Brasil | 0-10 | Bonus para eventos no Brasil |

## Deploy (Cloud Run)

- Backend: `Dockerfile` com uvicorn, `DATABASE_URL` como secret
- Cloud Scheduler: job diario `POST /api/events/sync` (ex: 03:00 BRT)
- Frontend: build estatico (`npm run build`) servido via Cloud Storage ou CDN

## Estrutura de Pastas

```
hackaton/
├── eventnexus/                  # Backend
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── models/event.py      # Pydantic schemas
│   │   ├── repositories/        # CRUD + dedup
│   │   ├── services/            # Discovery, normalization, scoring
│   │   ├── sources/             # 5 fontes de dados
│   │   └── routes/              # Endpoints
│   ├── migrations/              # SQL (idempotent)
│   ├── tests/
│   ├── Dockerfile
│   └── docker-compose.yml
├── eventnexus-frontend/         # Frontend
│   ├── src/
│   │   ├── components/          # SearchBar, FilterSidebar, EventCard, EventDetails, SyncButton
│   │   ├── pages/HomePage.tsx
│   │   ├── types.ts, api.ts
│   │   └── index.css            # Onfly brand theme
│   ├── package.json
│   └── vite.config.ts
├── docs/superpowers/
│   ├── specs/                   # Design spec
│   └── plans/                   # Implementation plans
└── old/                         # Codigo de referencia (nao usado em producao)
```

## Supabase

Conexao via connection pooling (PgBouncer):

```
DATABASE_URL=postgresql://postgres.prvljsmnyxvvgzmvsgzz:[PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
```

Conexao direta (para migrations):

```
DIRECT_URL=postgresql://postgres.prvljsmnyxvvgzmvsgzz:[PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:5432/postgres
```

## Licenca

Projeto interno — hackathon.
