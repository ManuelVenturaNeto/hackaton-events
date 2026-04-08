# Design: Duty of Care Travel Risk API

**Data:** 2026-04-06  
**Contexto:** Hackathon — API inteligente de riscos para destinos de viagem corporativa  
**Stack:** Python 3.12 + FastAPI + Cloud Run + Cloud Build + Firestore + BigQuery + Secret Manager

---

## 1. Visão Geral

API REST que agrega fontes públicas de risco de viagem corporativa e retorna um score normalizado (0-100) por país com breakdown por categoria. Deploy em produção na GCP via Cloud Run, com desenvolvimento e testes 100% locais antes do push.

**Endpoints:**
- `GET /risk/{country_code}` — score composto + breakdown + fontes usadas
- `GET /advisories/{country_code}` — lista de advisories do U.S. State Dept
- `GET /health` — liveness check

---

## 2. Arquitetura

```
LOCAL
  .env → uv run uvicorn → in-memory cache → testes manuais/pytest
  docker build + docker run → valida container antes do push

GCP (push na main)
  Cloud Build Trigger
    → docker build
    → push Artifact Registry
    → gcloud run deploy (Cloud Run)

  Cloud Run (FastAPI container)
    → secrets via Secret Manager
    → cache via Firestore
    → logs de eventos via BigQuery (fire-and-forget)
```

---

## 3. Fontes Externas e Graceful Degradation

Cada coletor é independente. Falhas não derrubam a API — o scorer usa o que estiver disponível.

| Fonte | Credencial | Sempre ativa? | Categoria |
|---|---|---|---|
| U.S. State Dept | Nenhuma | Sim | advisory_level |
| Open-Meteo | Nenhuma | Sim | storm, flood |
| GDELT | Nenhuma | Sim | civil_unrest |
| Amadeus GeoSure | AMADEUS_CLIENT_ID + SECRET | Não (opcional) | physical_safety, health_medical, political_freedom, theft_risk |
| ACLED | ACLED_API_KEY + EMAIL | Não (opcional) | conflict |

**Fluxo de coleta:**
```python
results = await asyncio.gather(
    state_dept.fetch(code),     # sempre tenta
    open_meteo.fetch(coords),   # sempre tenta
    gdelt.fetch(code),          # sempre tenta
    amadeus.fetch(code),        # só se AMADEUS_* presente
    acled.fetch(code),          # só se ACLED_* presente
    return_exceptions=True
)
```

**Response com transparência de fontes:**
```json
{
  "country_code": "BR",
  "score": 48,
  "risk_level": "medium",
  "score_confidence": "partial",
  "data_sources": ["state_dept", "open_meteo", "gdelt"],
  "sources_unavailable": ["amadeus_geosure", "acled"],
  "breakdown": { ... },
  "cached": false,
  "updated_at": "2026-04-06T17:00:00Z"
}
```

**`score_confidence`:**
- `"full"` — todas as 5 fontes responderam
- `"partial"` — 2-4 fontes responderam
- `"low"` — apenas State Dept respondeu (score baseado só em advisory_level)

---

## 4. Cache Dual-Mode

Controlado pela variável `CACHE_BACKEND`:

| Ambiente | CACHE_BACKEND | Implementação | TTL |
|---|---|---|---|
| Local | `memory` (padrão) | dict Python com timestamp | State Dept: 6h / Amadeus: 1h |
| GCP | `firestore` | documento Firestore com campo `expires_at` | State Dept: 6h / Amadeus: 1h |

`cache_factory.py` retorna a implementação correta via env var. O código da API não sabe qual backend está usando (interface comum).

**Chave de cache:** `risk:{country_code}` e `advisories:{country_code}`

---

## 5. BigQuery — Registro de Eventos

**Controlado por:** `BQ_LOGGING_ENABLED=false` (local) / `true` (GCP)

**Dataset:** `duty_of_care`  
**Tabela:** `risk_events` — particionada por `requested_at` (dia)

**Schema:**

| Campo | Tipo | Descrição |
|---|---|---|
| `request_id` | STRING | UUID v4 da request |
| `country_code` | STRING | ISO 3166-1 alpha-2 |
| `score` | FLOAT | Score final 0-100 |
| `risk_level` | STRING | low / medium / high / critical |
| `score_confidence` | STRING | full / partial / low |
| `data_sources` | ARRAY\<STRING\> | Fontes que responderam |
| `sources_unavailable` | ARRAY\<STRING\> | Fontes que falharam |
| `breakdown` | STRING | JSON serializado do breakdown |
| `cached` | BOOL | true se veio do cache |
| `requested_at` | TIMESTAMP | Timestamp da request |
| `response_ms` | INTEGER | Latência total em ms |

**Implementação:** `bigquery_logger.py` usa `asyncio.create_task()` — fire-and-forget. A resposta da API não aguarda o insert. Falhas no log são silenciosas (apenas logadas no stderr).

---

## 6. Estrutura de Arquivos

```
duty-of-care-api/
  src/
    api/
      routers/
        risk.py
        advisories.py
        health.py
    services/
      state_dept.py
      amadeus_client.py
      scorer.py
    models/
      risk_score.py       # inclui score_confidence, sources_unavailable
      advisory.py
    cache/
      memory_cache.py
      firestore_cache.py
      cache_factory.py    # retorna backend via CACHE_BACKEND env var
    collectors/
      weather.py          # Open-Meteo
      human_events.py     # ACLED + GDELT
    logging/
      bigquery_logger.py  # fire-and-forget, desabilitado localmente
    main.py
  infra/
    setup.sh              # script one-time: cria projeto GCP, habilita APIs, secrets
    cloudbuild.yaml       # pipeline CI/CD: build → push → deploy
    Dockerfile            # python:3.12-slim, porta 8080
  tests/
    test_scorer.py
    test_services.py
  pyproject.toml
  .env.example
  README.md
```

---

## 7. Infra GCP — Setup One-Time

Executado uma única vez via `infra/setup.sh`:

```bash
# 1. Criar projeto
gcloud projects create duty-of-care-api --name="Duty of Care API"
gcloud config set project duty-of-care-api

# 2. Habilitar APIs
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  bigquery.googleapis.com

# 3. Artifact Registry
gcloud artifacts repositories create duty-of-care \
  --repository-format=docker --location=us-central1

# 4. Secrets
echo -n "$AMADEUS_CLIENT_ID" | gcloud secrets create AMADEUS_CLIENT_ID --data-file=-
echo -n "$AMADEUS_CLIENT_SECRET" | gcloud secrets create AMADEUS_CLIENT_SECRET --data-file=-
echo -n "$ACLED_API_KEY" | gcloud secrets create ACLED_API_KEY --data-file=-
echo -n "$ACLED_EMAIL" | gcloud secrets create ACLED_EMAIL --data-file=-

# 5. Firestore (Native mode)
gcloud firestore databases create --location=nam5

# 6. BigQuery
bq mk --dataset duty-of-care-api:duty_of_care

# 7. IAM — Cloud Build service account
PROJECT_NUMBER=$(gcloud projects describe duty-of-care-api --format='value(projectNumber)')
SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding duty-of-care-api \
  --member="serviceAccount:${SA}" \
  --role="roles/run.admin"
gcloud projects add-iam-policy-binding duty-of-care-api \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding duty-of-care-api \
  --member="serviceAccount:${SA}" \
  --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding duty-of-care-api \
  --member="serviceAccount:${SA}" \
  --role="roles/bigquery.dataEditor"
```

---

## 8. Pipeline Cloud Build (`infra/cloudbuild.yaml`)

```yaml
substitutions:
  _REGION: us-central1
  _SERVICE: duty-of-care-api
  _REPO: duty-of-care
  _IMAGE: ${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/${_SERVICE}:$COMMIT_SHA

steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${_IMAGE}', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_IMAGE}']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE}'
      - '--image=${_IMAGE}'
      - '--region=${_REGION}'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-secrets=AMADEUS_CLIENT_ID=AMADEUS_CLIENT_ID:latest,AMADEUS_CLIENT_SECRET=AMADEUS_CLIENT_SECRET:latest,ACLED_API_KEY=ACLED_API_KEY:latest,ACLED_EMAIL=ACLED_EMAIL:latest'
      - '--set-env-vars=CACHE_BACKEND=firestore,BQ_LOGGING_ENABLED=true,GCP_PROJECT_ID=$PROJECT_ID'
```

**Trigger:** push na branch `main` via Cloud Build Trigger (configurado no console GCP ou via `gcloud builds triggers create`).

---

## 9. Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY src/ ./src/

ENV PORT=8080
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 10. Workflow do Desenvolvedor

```
# Desenvolvimento local
cp .env.example .env        # preencher credenciais
uv sync
uv run uvicorn src.main:app --reload --port 8000

# Testar container localmente
docker build -t duty-of-care-api .
docker run -p 8080:8080 --env-file .env duty-of-care-api

# Deploy produção
git push origin main         # Cloud Build assume daqui
```

---

## 11. Variáveis de Ambiente

| Variável | Local | GCP | Descrição |
|---|---|---|---|
| `AMADEUS_CLIENT_ID` | `.env` (opcional) | Secret Manager | Credencial Amadeus |
| `AMADEUS_CLIENT_SECRET` | `.env` (opcional) | Secret Manager | Credencial Amadeus |
| `ACLED_API_KEY` | `.env` (opcional) | Secret Manager | Credencial ACLED |
| `ACLED_EMAIL` | `.env` (opcional) | Secret Manager | Email registro ACLED |
| `CACHE_BACKEND` | `memory` | `firestore` | Backend de cache |
| `BQ_LOGGING_ENABLED` | `false` | `true` | Habilita log BigQuery |
| `GCP_PROJECT_ID` | não usado | ID do projeto GCP | Para Firestore e BigQuery |
| `OWM_API_KEY` | `.env` (opcional) | Secret Manager (opcional) | OpenWeatherMap |

---

## 12. Testes

### Cobertura por endpoint

Cada endpoint deve ter testes cobrindo **todos os HTTP status codes possíveis**:

**`GET /risk/{country_code}`**
- `200 OK` — resposta válida com score (fontes completas)
- `200 OK` — resposta com `score_confidence: "partial"` (algumas fontes falharam)
- `200 OK` — resposta com `score_confidence: "low"` (apenas State Dept)
- `422 Unprocessable Entity` — country_code inválido (ex: "ZZZ", "B", "1234")
- `503 Service Unavailable` — todas as fontes falharam simultaneamente

**`GET /advisories/{country_code}`**
- `200 OK` — lista de advisories retornada
- `404 Not Found` — país sem advisory registrado
- `422 Unprocessable Entity` — country_code inválido

**`GET /health`**
- `200 OK` — serviço saudável

### Estrutura de testes

```
tests/
  test_scorer.py          # unit: normalização e weighted average (sem I/O)
  test_services.py        # unit: mock httpx para cada coletor
  test_routers/
    test_risk.py          # todos os status codes de /risk/{country_code}
    test_advisories.py    # todos os status codes de /advisories/{country_code}
    test_health.py        # status code de /health
  conftest.py             # fixtures: TestClient, mocks de coletores, mock BigQuery
```

Todos os testes de router usam `httpx.AsyncClient` com `transport=ASGITransport(app=app)` — sem servidor real, sem I/O externo (coletores mockados via `pytest-mock`).

- Graceful degradation testada com fixtures que simulam falha de cada coletor individualmente
- Rodar localmente: `uv run pytest tests/ -v`

---

## 13. Testes na Esteira CI/CD

Os testes são **gate obrigatório** antes do deploy. O `cloudbuild.yaml` adiciona um step de testes **antes** do build da imagem Docker. Se os testes falharem, o pipeline aborta e o deploy não acontece.

**Step de testes no `cloudbuild.yaml` (inserido antes do `docker build`):**

```yaml
  - name: 'python:3.12-slim'
    entrypoint: bash
    args:
      - '-c'
      - |
        pip install uv -q &&
        uv sync --no-dev -q &&
        uv add --dev pytest pytest-asyncio pytest-mock httpx -q &&
        uv run pytest tests/ -v --tb=short
    env:
      - 'CACHE_BACKEND=memory'
      - 'BQ_LOGGING_ENABLED=false'
```

**Ordem dos steps no pipeline completo:**
1. `pytest` — roda todos os testes; falha = pipeline encerra aqui
2. `docker build` — só executa se os testes passaram
3. `docker push` — envia imagem para Artifact Registry
4. `gcloud run deploy` — deploy no Cloud Run
