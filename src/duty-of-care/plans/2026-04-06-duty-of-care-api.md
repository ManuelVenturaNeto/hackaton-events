# Duty of Care Travel Risk API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a FastAPI REST API that aggregates public travel risk data from multiple sources and returns a normalized 0-100 risk score per country, with CI/CD to GCP Cloud Run.

**Architecture:** FastAPI monolith with async parallel collectors (State Dept, Open-Meteo, GDELT, Amadeus, ACLED). Cache is dual-mode (in-memory locally, Firestore on GCP). Each API call logs a risk event to BigQuery asynchronously (fire-and-forget). Graceful degradation: any collector can fail without breaking the response.

**Tech Stack:** Python 3.12, FastAPI, httpx, pydantic v2, python-amadeus SDK, google-cloud-firestore, google-cloud-bigquery, pytest/pytest-asyncio/pytest-mock, Docker, Cloud Run, Cloud Build, Secret Manager, Firestore, BigQuery, Artifact Registry.

---

## File Map

```
duty-of-care-api/
  src/
    __init__.py
    main.py                          # FastAPI app, routers, CORS
    api/
      __init__.py
      routers/
        __init__.py
        health.py                    # GET /health
        advisories.py                # GET /advisories/{country_code}
        risk.py                      # GET /risk/{country_code}
    services/
      __init__.py
      state_dept.py                  # U.S. State Dept httpx client
      amadeus_client.py              # Amadeus SDK wrapper
      scorer.py                      # Normalizes all sources → 0-100 score
    models/
      __init__.py
      risk_score.py                  # RiskScore, Breakdown, RiskLevel, ScoreConfidence
      advisory.py                    # Advisory, AdvisorySource
    cache/
      __init__.py
      base.py                        # CacheBackend ABC
      memory_cache.py                # In-memory dict with TTL
      firestore_cache.py             # Firestore backend
      cache_factory.py               # Returns backend based on CACHE_BACKEND env var
    collectors/
      __init__.py
      weather.py                     # Open-Meteo: storm/flood severity
      human_events.py                # GDELT (civil_unrest) + ACLED (conflict)
    logging/
      __init__.py
      bigquery_logger.py             # Fire-and-forget BigQuery insert
  tests/
    __init__.py
    conftest.py                      # Shared fixtures: async_client, mocks
    test_scorer.py                   # Unit: scorer normalization
    test_services.py                 # Unit: collectors with mocked httpx
    test_routers/
      __init__.py
      test_health.py
      test_advisories.py
      test_risk.py
  infra/
    Dockerfile
    cloudbuild.yaml
    setup.sh
  pyproject.toml
  .env.example
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: all `__init__.py` files and empty directory structure

- [ ] **Step 1: Initialize project with uv**

```bash
uv init duty-of-care-api
cd duty-of-care-api
```

- [ ] **Step 2: Replace pyproject.toml content**

```toml
[project]
name = "duty-of-care-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.29",
    "httpx>=0.27",
    "pydantic>=2.7",
    "python-dotenv>=1.0",
    "amadeus>=9.0",
    "google-cloud-firestore>=2.16",
    "google-cloud-bigquery>=3.20",
]

[dependency-groups]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.14",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

Expected: lock file created, dependencies installed.

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p src/api/routers src/services src/models src/cache src/collectors src/logging
mkdir -p tests/test_routers infra
touch src/__init__.py src/api/__init__.py src/api/routers/__init__.py
touch src/services/__init__.py src/models/__init__.py src/cache/__init__.py
touch src/collectors/__init__.py src/logging/__init__.py
touch tests/__init__.py tests/test_routers/__init__.py
```

- [ ] **Step 5: Create .env.example**

```bash
cat > .env.example << 'EOF'
# Amadeus API (optional — get free credentials at developers.amadeus.com)
AMADEUS_CLIENT_ID=
AMADEUS_CLIENT_SECRET=

# ACLED API (optional — register at acleddata.com/access-data)
ACLED_API_KEY=
ACLED_EMAIL=

# OpenWeatherMap (optional — openweathermap.org free tier)
OWM_API_KEY=

# Cache backend: "memory" (local) or "firestore" (GCP)
CACHE_BACKEND=memory

# BigQuery logging: "false" (local) or "true" (GCP)
BQ_LOGGING_ENABLED=false

# GCP project ID (only needed when CACHE_BACKEND=firestore or BQ_LOGGING_ENABLED=true)
GCP_PROJECT_ID=
EOF
```

- [ ] **Step 6: Copy .env.example to .env**

```bash
cp .env.example .env
```

- [ ] **Step 7: Commit**

```bash
git init
git add .
git commit -m "feat: initial project scaffold"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `src/models/advisory.py`
- Create: `src/models/risk_score.py`

- [ ] **Step 1: Write advisory model**

`src/models/advisory.py`:
```python
from pydantic import BaseModel
from typing import Optional


class Advisory(BaseModel):
    source: str
    level: int
    title: str
    updated_at: str
    url: str


class AdvisoryResponse(BaseModel):
    country_code: str
    country_name: str
    advisories: list[Advisory]
    data_sources: list[str]
    cached: bool = False
    updated_at: str
```

- [ ] **Step 2: Write risk score model**

`src/models/risk_score.py`:
```python
from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ScoreConfidence(str, Enum):
    full = "full"
    partial = "partial"
    low = "low"


class Breakdown(BaseModel):
    advisory_level: Optional[float] = None
    physical_safety: Optional[float] = None
    health_medical: Optional[float] = None
    political_freedom: Optional[float] = None
    theft_risk: Optional[float] = None
    storm: Optional[float] = None
    flood: Optional[float] = None
    civil_unrest: Optional[float] = None
    conflict: Optional[float] = None


class RiskScore(BaseModel):
    country_code: str
    country_name: str
    score: float
    risk_level: RiskLevel
    score_confidence: ScoreConfidence
    breakdown: Breakdown
    advisories: list
    data_sources: list[str]
    sources_unavailable: list[str]
    cached: bool = False
    updated_at: str
```

- [ ] **Step 3: Add country lookup utility**

`src/models/countries.py`:
```python
COUNTRY_NAMES: dict[str, str] = {
    "BR": "Brazil", "CO": "Colombia", "MX": "Mexico",
    "AR": "Argentina", "CL": "Chile", "PE": "Peru",
    "US": "United States", "GB": "United Kingdom",
    "DE": "Germany", "FR": "France", "ES": "Spain",
    "IT": "Italy", "PT": "Portugal", "JP": "Japan",
    "CN": "China", "IN": "India", "AU": "Australia",
    "ZA": "South Africa", "NG": "Nigeria", "EG": "Egypt",
    "UA": "Ukraine", "RU": "Russia", "TR": "Turkey",
    "SA": "Saudi Arabia", "IL": "Israel", "PK": "Pakistan",
    "AF": "Afghanistan", "IQ": "Iraq", "SY": "Syria",
    "VE": "Venezuela", "HT": "Haiti",
}

# Capital city coordinates for weather lookups
COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "BR": (-15.78, -47.93), "CO": (4.71, -74.07),
    "MX": (19.43, -99.13), "AR": (-34.60, -58.38),
    "CL": (-33.46, -70.65), "PE": (-12.05, -77.04),
    "US": (38.90, -77.04), "GB": (51.51, -0.13),
    "DE": (52.52, 13.40), "FR": (48.85, 2.35),
    "ES": (40.42, -3.70), "IT": (41.90, 12.49),
    "PT": (38.72, -9.14), "JP": (35.69, 139.69),
    "CN": (39.91, 116.39), "IN": (28.61, 77.21),
    "AU": (-35.28, 149.13), "ZA": (-25.75, 28.19),
    "NG": (9.08, 7.40), "EG": (30.06, 31.25),
    "UA": (50.45, 30.52), "RU": (55.75, 37.62),
    "TR": (39.92, 32.85), "SA": (24.69, 46.72),
    "IL": (31.77, 35.22), "PK": (33.72, 73.04),
    "AF": (34.53, 69.17), "IQ": (33.34, 44.40),
    "SY": (33.51, 36.29), "VE": (10.49, -66.88),
    "HT": (18.54, -72.34),
}


def get_country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def get_country_coords(code: str) -> tuple[float, float]:
    return COUNTRY_COORDS.get(code, (0.0, 0.0))
```

- [ ] **Step 4: Add touch to __init__.py for models**

`src/models/__init__.py`:
```python
from .risk_score import RiskScore, RiskLevel, ScoreConfidence, Breakdown
from .advisory import Advisory, AdvisoryResponse
from .countries import get_country_name, get_country_coords
```

- [ ] **Step 5: Commit**

```bash
git add src/models/
git commit -m "feat: add pydantic models and country lookup"
```

---

## Task 3: Cache Abstraction + Memory Backend

**Files:**
- Create: `src/cache/base.py`
- Create: `src/cache/memory_cache.py`
- Create: `src/cache/cache_factory.py`

- [ ] **Step 1: Write failing test for memory cache**

`tests/test_services.py` (create file):
```python
import pytest
import asyncio
from src.cache.memory_cache import MemoryCache


@pytest.mark.asyncio
async def test_memory_cache_set_and_get():
    cache = MemoryCache()
    await cache.set("key1", {"data": "value"}, ttl_seconds=3600)
    result = await cache.get("key1")
    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_memory_cache_returns_none_for_missing_key():
    cache = MemoryCache()
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_memory_cache_expires_entry():
    cache = MemoryCache()
    await cache.set("key_exp", "value", ttl_seconds=0)
    await asyncio.sleep(0.01)
    result = await cache.get("key_exp")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py::test_memory_cache_set_and_get -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.cache.memory_cache'`

- [ ] **Step 3: Write cache base class**

`src/cache/base.py`:
```python
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        ...
```

- [ ] **Step 4: Write memory cache**

`src/cache/memory_cache.py`:
```python
import time
from typing import Any, Optional
from .base import CacheBackend


class MemoryCache(CacheBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (value, time.time() + ttl_seconds)
```

- [ ] **Step 5: Write cache factory**

`src/cache/cache_factory.py`:
```python
import os
from .base import CacheBackend
from .memory_cache import MemoryCache


def get_cache() -> CacheBackend:
    backend = os.getenv("CACHE_BACKEND", "memory")
    if backend == "firestore":
        from .firestore_cache import FirestoreCache
        return FirestoreCache()
    return MemoryCache()
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_services.py -k "cache" -v
```

Expected: 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/cache/ tests/test_services.py
git commit -m "feat: cache abstraction with in-memory backend"
```

---

## Task 4: Scorer + Unit Tests

**Files:**
- Create: `src/services/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write failing tests for scorer**

`tests/test_scorer.py`:
```python
import pytest
from src.services.scorer import compute_score, normalize_advisory, risk_level_from_score
from src.models.risk_score import RiskLevel, ScoreConfidence


def test_normalize_advisory_level_1_returns_0():
    assert normalize_advisory(1) == 0.0


def test_normalize_advisory_level_2_returns_33():
    assert normalize_advisory(2) == pytest.approx(33.3, abs=0.5)


def test_normalize_advisory_level_3_returns_66():
    assert normalize_advisory(3) == pytest.approx(66.7, abs=0.5)


def test_normalize_advisory_level_4_returns_100():
    assert normalize_advisory(4) == 100.0


def test_risk_level_low():
    assert risk_level_from_score(20) == RiskLevel.low


def test_risk_level_medium():
    assert risk_level_from_score(40) == RiskLevel.medium


def test_risk_level_high():
    assert risk_level_from_score(60) == RiskLevel.high


def test_risk_level_critical():
    assert risk_level_from_score(80) == RiskLevel.critical


def test_compute_score_state_dept_only_returns_low_confidence():
    result = compute_score(advisory_level=2)
    assert result is not None
    assert result["score_confidence"] == ScoreConfidence.low
    assert result["score"] == pytest.approx(33.3, abs=1.0)
    assert "state_dept" in result["data_sources"]


def test_compute_score_with_amadeus_returns_partial_confidence():
    result = compute_score(
        advisory_level=2,
        physical_safety=60.0,
        health_medical=70.0,
        political_freedom=65.0,
        theft_risk=55.0,
    )
    assert result["score_confidence"] == ScoreConfidence.partial
    assert "amadeus_geosure" in result["data_sources"]


def test_compute_score_all_sources_returns_full_confidence():
    result = compute_score(
        advisory_level=2,
        physical_safety=60.0,
        health_medical=70.0,
        political_freedom=65.0,
        theft_risk=55.0,
        storm_severity=1.0,
        flood_severity=0.5,
        civil_unrest_severity=2.0,
        conflict_severity=1.0,
    )
    assert result["score_confidence"] == ScoreConfidence.full
    assert len(result["data_sources"]) == 5


def test_compute_score_no_sources_returns_none():
    result = compute_score()
    assert result is None


def test_compute_score_breakdown_contains_active_sources():
    result = compute_score(advisory_level=3, storm_severity=2.0)
    assert result["breakdown"]["advisory_level"] is not None
    assert result["breakdown"]["storm"] is not None
    assert result["breakdown"]["physical_safety"] is None


def test_sources_unavailable_listed_when_optional_missing():
    result = compute_score(advisory_level=2)
    assert "amadeus_geosure" in result["sources_unavailable"]
    assert "acled" in result["sources_unavailable"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement scorer**

`src/services/scorer.py`:
```python
from typing import Optional
from src.models.risk_score import RiskLevel, ScoreConfidence, Breakdown

# Advisory: 1→0, 2→33.3, 3→66.7, 4→100
_ADVISORY_MAP = {1: 0.0, 2: 33.3, 3: 66.7, 4: 100.0}

# Weights for each component (must sum to 1.0 when all present)
_WEIGHTS = {
    "advisory":         0.28,
    "physical_safety":  0.10,
    "health_medical":   0.08,
    "political_freedom":0.08,
    "theft_risk":       0.08,
    "conflict":         0.14,  # ACLED — highest risk multiplier
    "civil_unrest":     0.08,  # GDELT
    "storm":            0.08,
    "flood":            0.08,
}

_AMADEUS_FIELDS = {"physical_safety", "health_medical", "political_freedom", "theft_risk"}
_ALL_SOURCES = {"state_dept", "amadeus_geosure", "open_meteo", "gdelt", "acled"}


def normalize_advisory(level: int) -> float:
    return _ADVISORY_MAP.get(level, 0.0)


def risk_level_from_score(score: float) -> RiskLevel:
    if score <= 25:
        return RiskLevel.low
    if score <= 50:
        return RiskLevel.medium
    if score <= 75:
        return RiskLevel.high
    return RiskLevel.critical


def compute_score(
    advisory_level: Optional[int] = None,
    physical_safety: Optional[float] = None,
    health_medical: Optional[float] = None,
    political_freedom: Optional[float] = None,
    theft_risk: Optional[float] = None,
    storm_severity: Optional[float] = None,
    flood_severity: Optional[float] = None,
    civil_unrest_severity: Optional[float] = None,
    conflict_severity: Optional[float] = None,
) -> Optional[dict]:
    """Returns scored dict or None if no sources available."""
    components: dict[str, float] = {}
    data_sources: list[str] = []

    if advisory_level is not None:
        components["advisory"] = normalize_advisory(advisory_level)
        data_sources.append("state_dept")

    has_amadeus = all(
        v is not None for v in [physical_safety, health_medical, political_freedom, theft_risk]
    )
    if has_amadeus:
        # GeoSure: higher score = safer, so risk = 100 - score
        components["physical_safety"] = 100.0 - physical_safety  # type: ignore[operator]
        components["health_medical"] = 100.0 - health_medical    # type: ignore[operator]
        components["political_freedom"] = 100.0 - political_freedom  # type: ignore[operator]
        components["theft_risk"] = 100.0 - theft_risk            # type: ignore[operator]
        data_sources.append("amadeus_geosure")

    has_weather = storm_severity is not None or flood_severity is not None
    if has_weather:
        if storm_severity is not None:
            components["storm"] = storm_severity * 20.0
        if flood_severity is not None:
            components["flood"] = flood_severity * 20.0
        data_sources.append("open_meteo")

    if civil_unrest_severity is not None:
        components["civil_unrest"] = civil_unrest_severity * 20.0
        data_sources.append("gdelt")

    if conflict_severity is not None:
        components["conflict"] = conflict_severity * 20.0
        data_sources.append("acled")

    if not components:
        return None

    # Normalized weighted average
    active_weights = {k: _WEIGHTS[k] for k in components if k in _WEIGHTS}
    total_weight = sum(active_weights.values())
    score = sum(
        components[k] * active_weights[k] / total_weight
        for k in components
        if k in active_weights
    )
    score = round(min(100.0, max(0.0, score)), 1)

    # Score confidence
    source_count = len(data_sources)
    if source_count == 5:
        confidence = ScoreConfidence.full
    elif source_count == 1 and "state_dept" in data_sources:
        confidence = ScoreConfidence.low
    else:
        confidence = ScoreConfidence.partial

    sources_unavailable = [s for s in _ALL_SOURCES if s not in data_sources]

    breakdown = Breakdown(
        advisory_level=components.get("advisory"),
        physical_safety=components.get("physical_safety"),
        health_medical=components.get("health_medical"),
        political_freedom=components.get("political_freedom"),
        theft_risk=components.get("theft_risk"),
        storm=components.get("storm"),
        flood=components.get("flood"),
        civil_unrest=components.get("civil_unrest"),
        conflict=components.get("conflict"),
    )

    return {
        "score": score,
        "risk_level": risk_level_from_score(score),
        "score_confidence": confidence,
        "breakdown": breakdown,
        "data_sources": data_sources,
        "sources_unavailable": sources_unavailable,
    }
```

- [ ] **Step 4: Run all scorer tests**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: all 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/scorer.py tests/test_scorer.py
git commit -m "feat: scorer with weighted average and graceful degradation"
```

---

## Task 5: State Dept Service

**Files:**
- Create: `src/services/state_dept.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_services.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.services.state_dept import fetch_advisory


@pytest.mark.asyncio
async def test_state_dept_returns_advisory_for_known_country(respx_mock=None):
    mock_response = {
        "data": {
            "BR": {
                "advisoryState": 2,
                "name": "Exercise Increased Caution",
                "url": "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/brazil-travel-advisory.html",
                "dateUpdated": "2026-03-15"
            }
        }
    }
    with patch("src.services.state_dept.httpx.AsyncClient") as mock_client_cls:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = AsyncMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await fetch_advisory("BR")

    assert result is not None
    assert result.advisory_level == 2
    assert "Brazil" in result.title or result.advisory_level == 2


@pytest.mark.asyncio
async def test_state_dept_returns_none_on_http_error():
    with patch("src.services.state_dept.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("Connection error")
        mock_client_cls.return_value = mock_client

        result = await fetch_advisory("BR")

    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "state_dept" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement State Dept service**

`src/services/state_dept.py`:
```python
import httpx
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_STATE_DEPT_URL = "https://cadataapi.state.gov/api/TravelAdvisories/data/Advisories"


@dataclass
class StateDeptResult:
    advisory_level: int
    title: str
    url: str
    updated_at: str


async def fetch_advisory(country_code: str) -> Optional[StateDeptResult]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_STATE_DEPT_URL)
            resp.raise_for_status()
            data = resp.json()

        country_data = data.get("data", {}).get(country_code)
        if not country_data:
            return None

        return StateDeptResult(
            advisory_level=int(country_data.get("advisoryState", 1)),
            title=country_data.get("name", ""),
            url=country_data.get("url", ""),
            updated_at=country_data.get("dateUpdated", ""),
        )
    except Exception as e:
        logger.warning("State Dept fetch failed for %s: %s", country_code, e)
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "state_dept" -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/state_dept.py tests/test_services.py
git commit -m "feat: U.S. State Dept advisory service"
```

---

## Task 6: Weather Collector (Open-Meteo)

**Files:**
- Create: `src/collectors/weather.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_services.py`:
```python
from unittest.mock import AsyncMock, patch
from src.collectors.weather import fetch_weather_events


@pytest.mark.asyncio
async def test_weather_returns_severity_for_storm_codes():
    # WMO code 95 = thunderstorm
    mock_response = {
        "hourly": {
            "weathercode": [95, 95, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "precipitation": [10.0] * 24,
            "windspeed_10m": [30.0] * 24,
        }
    }
    with patch("src.collectors.weather.httpx.AsyncClient") as mock_client_cls:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = AsyncMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await fetch_weather_events("BR")

    assert result is not None
    assert result.storm_severity > 0


@pytest.mark.asyncio
async def test_weather_returns_none_on_error():
    with patch("src.collectors.weather.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("timeout")
        mock_client_cls.return_value = mock_client

        result = await fetch_weather_events("BR")

    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "weather" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement weather collector**

`src/collectors/weather.py`:
```python
import httpx
import logging
from dataclasses import dataclass
from typing import Optional
from src.models.countries import get_country_coords

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO codes that indicate storm conditions (≥80)
_STORM_CODES = {80, 81, 82, 95, 96, 99}
# WMO codes that indicate heavy rain/flood risk (61-67, 71-77, 85-86)
_FLOOD_CODES = set(range(61, 68)) | set(range(71, 78)) | {85, 86}


@dataclass
class WeatherResult:
    storm_severity: float  # 0-5
    flood_severity: float  # 0-5


def _severity_from_codes(codes: list[int], target_codes: set[int]) -> float:
    hits = sum(1 for c in codes if c in target_codes)
    ratio = hits / max(len(codes), 1)
    return min(5.0, round(ratio * 5 * 4, 1))  # scale: >25% of hours → severity 5


async def fetch_weather_events(country_code: str) -> Optional[WeatherResult]:
    lat, lon = get_country_coords(country_code)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "weathercode,precipitation,windspeed_10m",
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        codes = data.get("hourly", {}).get("weathercode", [])
        storm = _severity_from_codes(codes, _STORM_CODES)
        flood = _severity_from_codes(codes, _FLOOD_CODES)
        return WeatherResult(storm_severity=storm, flood_severity=flood)
    except Exception as e:
        logger.warning("Open-Meteo fetch failed for %s: %s", country_code, e)
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "weather" -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/collectors/weather.py tests/test_services.py
git commit -m "feat: Open-Meteo weather collector"
```

---

## Task 7: Human Events Collector (GDELT + ACLED)

**Files:**
- Create: `src/collectors/human_events.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_services.py`:
```python
from src.collectors.human_events import fetch_gdelt, fetch_acled
import os


@pytest.mark.asyncio
async def test_gdelt_returns_civil_unrest_severity():
    mock_response = {
        "features": [
            {"properties": {"tone": -25.0}},
            {"properties": {"tone": -30.0}},
            {"properties": {"tone": -5.0}},
        ]
    }
    with patch("src.collectors.human_events.httpx.AsyncClient") as mock_client_cls:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = AsyncMock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await fetch_gdelt("BR")

    assert result is not None
    assert result.civil_unrest_severity > 0


@pytest.mark.asyncio
async def test_gdelt_returns_none_on_error():
    with patch("src.collectors.human_events.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("error")
        mock_client_cls.return_value = mock_client

        result = await fetch_gdelt("BR")

    assert result is None


@pytest.mark.asyncio
async def test_acled_returns_none_when_no_credentials(monkeypatch):
    monkeypatch.delenv("ACLED_API_KEY", raising=False)
    monkeypatch.delenv("ACLED_EMAIL", raising=False)
    result = await fetch_acled("BR")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "gdelt or acled" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement human events collector**

`src/collectors/human_events.py`:
```python
import httpx
import os
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_GDELT_URL = "https://api.gdeltproject.org/api/v2/geo/geo"
_ACLED_URL = "https://api.acleddata.com/acled/read"

COUNTRY_NAMES_FOR_QUERY = {
    "BR": "Brazil", "CO": "Colombia", "MX": "Mexico", "AR": "Argentina",
    "CL": "Chile", "PE": "Peru", "US": "United States", "GB": "United Kingdom",
    "DE": "Germany", "FR": "France", "UA": "Ukraine", "RU": "Russia",
    "AF": "Afghanistan", "IQ": "Iraq", "SY": "Syria", "VE": "Venezuela",
}


@dataclass
class GdeltResult:
    civil_unrest_severity: float  # 0-5


@dataclass
class AcledResult:
    conflict_severity: float  # 0-5


async def fetch_gdelt(country_code: str) -> Optional[GdeltResult]:
    country_name = COUNTRY_NAMES_FOR_QUERY.get(country_code, country_code)
    query = f"(protest OR riot OR strike OR unrest) {country_name}"
    since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y%m%d%H%M%S")
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": 250,
        "startdatetime": since,
        "format": "GeoJSON",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_GDELT_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        if not features:
            return GdeltResult(civil_unrest_severity=0.0)

        tones = [
            f["properties"].get("tone", 0.0)
            for f in features
            if isinstance(f.get("properties", {}).get("tone"), (int, float))
        ]
        if not tones:
            return GdeltResult(civil_unrest_severity=0.0)

        avg_tone = sum(tones) / len(tones)
        # tone is negative for bad news; below -20 = high unrest
        severity = min(5.0, max(0.0, (-avg_tone - 5) / 5))
        return GdeltResult(civil_unrest_severity=round(severity, 2))
    except Exception as e:
        logger.warning("GDELT fetch failed for %s: %s", country_code, e)
        return None


async def fetch_acled(country_code: str) -> Optional[AcledResult]:
    api_key = os.getenv("ACLED_API_KEY")
    email = os.getenv("ACLED_EMAIL")
    if not api_key or not email:
        return None

    country_name = COUNTRY_NAMES_FOR_QUERY.get(country_code)
    if not country_name:
        return None

    since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    params = {
        "key": api_key,
        "email": email,
        "country": country_name,
        "event_date": since,
        "event_date_where": ">=",
        "limit": 500,
        "fields": "event_type|fatalities|event_date",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_ACLED_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        events = data.get("data", [])
        if not events:
            return AcledResult(conflict_severity=0.0)

        max_fatalities = max(
            int(e.get("fatalities", 0)) for e in events
        )
        if max_fatalities == 0:
            severity = 2.0
        elif max_fatalities <= 10:
            severity = 3.0
        elif max_fatalities <= 50:
            severity = 4.0
        else:
            severity = 5.0

        return AcledResult(conflict_severity=severity)
    except Exception as e:
        logger.warning("ACLED fetch failed for %s: %s", country_code, e)
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "gdelt or acled" -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/collectors/human_events.py tests/test_services.py
git commit -m "feat: GDELT and ACLED human events collectors"
```

---

## Task 8: Amadeus Client

**Files:**
- Create: `src/services/amadeus_client.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_services.py`:
```python
from src.services.amadeus_client import fetch_geosure


@pytest.mark.asyncio
async def test_amadeus_returns_none_when_no_credentials(monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    result = await fetch_geosure("BR")
    assert result is None


@pytest.mark.asyncio
async def test_amadeus_returns_geosure_scores(monkeypatch):
    monkeypatch.setenv("AMADEUS_CLIENT_ID", "test_id")
    monkeypatch.setenv("AMADEUS_CLIENT_SECRET", "test_secret")

    mock_safe_place_data = [
        {
            "geoCode": {"latitude": -15.78, "longitude": -47.93},
            "safetyScores": {
                "physicalHarm": 42,
                "theft": 62,
                "politicalFreedom": 35,
                "medicalDifficulty": 45,
            },
        }
    ]

    with patch("src.services.amadeus_client.Client") as mock_amadeus_cls:
        mock_amadeus = mock_amadeus_cls.return_value
        mock_response = AsyncMock()
        mock_response.data = mock_safe_place_data
        mock_amadeus.safety.safety_rated_locations.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_geosure("BR")

    assert result is not None
    assert 0 <= result.physical_safety <= 100
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "amadeus" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Amadeus client**

`src/services/amadeus_client.py`:
```python
import os
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from src.models.countries import get_country_coords

logger = logging.getLogger(__name__)


@dataclass
class AmadeusResult:
    physical_safety: float   # 0-100 (higher = safer, GeoSure scale)
    health_medical: float
    political_freedom: float
    theft_risk: float


async def fetch_geosure(country_code: str) -> Optional[AmadeusResult]:
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    try:
        from amadeus import Client, ResponseError
        amadeus = Client(
            client_id=client_id,
            client_secret=client_secret,
            hostname="test",
        )
        lat, lon = get_country_coords(country_code)
        response = await asyncio.to_thread(
            amadeus.safety.safety_rated_locations.get,
            latitude=lat,
            longitude=lon,
            radius=160,
        )
        if not response.data:
            return None

        # Average scores across returned locations
        scores: dict[str, list[float]] = {
            "physical": [], "theft": [], "political": [], "medical": []
        }
        for loc in response.data:
            s = loc.get("safetyScores", {})
            if s.get("physicalHarm") is not None:
                scores["physical"].append(float(s["physicalHarm"]))
            if s.get("theft") is not None:
                scores["theft"].append(float(s["theft"]))
            if s.get("politicalFreedom") is not None:
                scores["political"].append(float(s["politicalFreedom"]))
            if s.get("medicalDifficulty") is not None:
                scores["medical"].append(float(s["medicalDifficulty"]))

        def avg(lst: list[float]) -> float:
            return sum(lst) / len(lst) if lst else 50.0

        # GeoSure scores: lower physicalHarm = safer → invert for physical_safety
        return AmadeusResult(
            physical_safety=100.0 - avg(scores["physical"]),
            health_medical=100.0 - avg(scores["medical"]),
            political_freedom=avg(scores["political"]),
            theft_risk=100.0 - avg(scores["theft"]),
        )
    except Exception as e:
        logger.warning("Amadeus fetch failed for %s: %s", country_code, e)
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "amadeus" -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/amadeus_client.py tests/test_services.py
git commit -m "feat: Amadeus GeoSure client with optional credential handling"
```

---

## Task 9: Firestore Cache Backend

**Files:**
- Create: `src/cache/firestore_cache.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_services.py`:
```python
from unittest.mock import MagicMock, patch, AsyncMock
from src.cache.firestore_cache import FirestoreCache
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_firestore_cache_returns_none_for_missing_key():
    with patch("src.cache.firestore_cache.firestore") as mock_fs:
        mock_doc = MagicMock()
        mock_doc.get.return_value = MagicMock(exists=False)
        mock_fs.Client.return_value.collection.return_value.document.return_value = mock_doc
        cache = FirestoreCache()
        result = await cache.get("missing_key")
    assert result is None


@pytest.mark.asyncio
async def test_firestore_cache_returns_none_for_expired_key():
    with patch("src.cache.firestore_cache.firestore") as mock_fs:
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_snap = MagicMock(exists=True)
        mock_snap.to_dict.return_value = {
            "value": "data",
            "expires_at": expired_time,
        }
        mock_doc = MagicMock()
        mock_doc.get.return_value = mock_snap
        mock_fs.Client.return_value.collection.return_value.document.return_value = mock_doc
        cache = FirestoreCache()
        result = await cache.get("expired_key")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "firestore" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Firestore cache**

`src/cache/firestore_cache.py`:
```python
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from .base import CacheBackend

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore
except ImportError:
    firestore = None  # type: ignore[assignment]


class FirestoreCache(CacheBackend):
    _COLLECTION = "risk_cache"

    def __init__(self) -> None:
        if firestore is None:
            raise RuntimeError("google-cloud-firestore not installed")
        self._client = firestore.Client()

    async def get(self, key: str) -> Optional[Any]:
        try:
            doc_ref = self._client.collection(self._COLLECTION).document(key)
            snap = await asyncio.to_thread(doc_ref.get)
            if not snap.exists:
                return None
            data = snap.to_dict()
            expires_at = data.get("expires_at")
            if expires_at and datetime.now(timezone.utc) > expires_at:
                return None
            raw = data.get("value")
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception as e:
            logger.warning("Firestore cache get failed for %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        try:
            doc_ref = self._client.collection(self._COLLECTION).document(key)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            await asyncio.to_thread(
                doc_ref.set,
                {"value": json.dumps(value), "expires_at": expires_at},
            )
        except Exception as e:
            logger.warning("Firestore cache set failed for %s: %s", key, e)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "firestore" -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cache/firestore_cache.py tests/test_services.py
git commit -m "feat: Firestore cache backend"
```

---

## Task 10: BigQuery Logger

**Files:**
- Create: `src/logging/bigquery_logger.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_services.py`:
```python
from src.logging.bigquery_logger import log_risk_event
import asyncio


@pytest.mark.asyncio
async def test_bigquery_logger_does_nothing_when_disabled(monkeypatch):
    monkeypatch.setenv("BQ_LOGGING_ENABLED", "false")
    # Should not raise, should complete silently
    await log_risk_event(
        request_id="test-id",
        country_code="BR",
        score=48.0,
        risk_level="medium",
        score_confidence="partial",
        data_sources=["state_dept"],
        sources_unavailable=["amadeus_geosure"],
        breakdown={},
        cached=False,
        response_ms=100,
    )


@pytest.mark.asyncio
async def test_bigquery_logger_does_not_raise_on_error(monkeypatch):
    monkeypatch.setenv("BQ_LOGGING_ENABLED", "true")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    with patch("src.logging.bigquery_logger.bigquery") as mock_bq:
        mock_bq.Client.side_effect = Exception("connection failed")
        # Should not raise — fire-and-forget
        await log_risk_event(
            request_id="test-id",
            country_code="BR",
            score=48.0,
            risk_level="medium",
            score_confidence="partial",
            data_sources=["state_dept"],
            sources_unavailable=[],
            breakdown={},
            cached=False,
            response_ms=150,
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services.py -k "bigquery" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement BigQuery logger**

`src/logging/bigquery_logger.py`:
```python
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None  # type: ignore[assignment]

_DATASET = "duty_of_care"
_TABLE = "risk_events"


async def log_risk_event(
    request_id: str,
    country_code: str,
    score: float,
    risk_level: str,
    score_confidence: str,
    data_sources: list[str],
    sources_unavailable: list[str],
    breakdown: dict,
    cached: bool,
    response_ms: int,
) -> None:
    enabled = os.getenv("BQ_LOGGING_ENABLED", "false").lower() == "true"
    if not enabled:
        return

    project = os.getenv("GCP_PROJECT_ID", "")
    if not project or bigquery is None:
        return

    row = {
        "request_id": request_id,
        "country_code": country_code,
        "score": score,
        "risk_level": risk_level,
        "score_confidence": score_confidence,
        "data_sources": data_sources,
        "sources_unavailable": sources_unavailable,
        "breakdown": json.dumps(breakdown),
        "cached": cached,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "response_ms": response_ms,
    }
    try:
        client = bigquery.Client(project=project)
        table_id = f"{project}.{_DATASET}.{_TABLE}"
        await asyncio.to_thread(client.insert_rows_json, table_id, [row])
    except Exception as e:
        logger.warning("BigQuery log failed: %s", e)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_services.py -k "bigquery" -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/logging/bigquery_logger.py tests/test_services.py
git commit -m "feat: BigQuery fire-and-forget event logger"
```

---

## Task 11: Test Infrastructure (conftest.py)

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Write conftest.py**

`tests/conftest.py`:
```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_state_dept_ok():
    from src.services.state_dept import StateDeptResult
    result = StateDeptResult(
        advisory_level=2,
        title="Exercise Increased Caution",
        url="https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/brazil-travel-advisory.html",
        updated_at="2026-03-15",
    )
    with patch("src.api.routers.risk.fetch_advisory", return_value=result) as m, \
         patch("src.api.routers.advisories.fetch_advisory", return_value=result):
        yield m


@pytest.fixture
def mock_state_dept_none():
    with patch("src.api.routers.risk.fetch_advisory", return_value=None), \
         patch("src.api.routers.advisories.fetch_advisory", return_value=None):
        yield


@pytest.fixture
def mock_weather_ok():
    from src.collectors.weather import WeatherResult
    result = WeatherResult(storm_severity=1.0, flood_severity=0.5)
    with patch("src.api.routers.risk.fetch_weather_events", return_value=result):
        yield


@pytest.fixture
def mock_weather_none():
    with patch("src.api.routers.risk.fetch_weather_events", return_value=None):
        yield


@pytest.fixture
def mock_gdelt_ok():
    from src.collectors.human_events import GdeltResult
    result = GdeltResult(civil_unrest_severity=2.0)
    with patch("src.api.routers.risk.fetch_gdelt", return_value=result):
        yield


@pytest.fixture
def mock_amadeus_none():
    with patch("src.api.routers.risk.fetch_geosure", return_value=None):
        yield


@pytest.fixture
def mock_acled_none():
    with patch("src.api.routers.risk.fetch_acled", return_value=None):
        yield


@pytest.fixture
def mock_bq():
    with patch("src.api.routers.risk.log_risk_event", new_callable=AsyncMock):
        yield


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    with patch("src.api.routers.risk.get_cache", return_value=cache), \
         patch("src.api.routers.advisories.get_cache", return_value=cache):
        yield cache


@pytest_asyncio.fixture
async def async_client(mock_bq, mock_cache):
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

- [ ] **Step 2: Verify conftest imports don't error before main.py exists (will fix after main.py)**

Skip for now — conftest will work once main.py is in place (Task 15).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: shared fixtures for router tests"
```

---

## Task 12: Health Router + Tests

**Files:**
- Create: `src/api/routers/health.py`
- Create: `tests/test_routers/test_health.py`

- [ ] **Step 1: Write failing test**

`tests/test_routers/test_health.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_returns_200():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_routers/test_health.py -v
```

Expected: FAIL with `ModuleNotFoundError` (main.py not yet created)

- [ ] **Step 3: Create health router**

`src/api/routers/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Create minimal main.py to unblock health test**

`src/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from src.api.routers import health, advisories, risk

app = FastAPI(
    title="Duty of Care Travel Risk API",
    description="Real-time travel risk scoring for corporate destinations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(advisories.router, prefix="/advisories")
app.include_router(risk.router, prefix="/risk")
```

Note: advisories.py and risk.py must exist (even if empty) for this import to work — create stubs now:

`src/api/routers/advisories.py` (stub):
```python
from fastapi import APIRouter
router = APIRouter()
```

`src/api/routers/risk.py` (stub):
```python
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 5: Run health test**

```bash
uv run pytest tests/test_routers/test_health.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/api/routers/health.py src/api/routers/advisories.py src/api/routers/risk.py src/main.py tests/test_routers/test_health.py
git commit -m "feat: health router and FastAPI app entry point"
```

---

## Task 13: Advisories Router + Tests

**Files:**
- Modify: `src/api/routers/advisories.py`
- Create: `tests/test_routers/test_advisories.py`

- [ ] **Step 1: Write failing tests**

`tests/test_routers/test_advisories.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from src.services.state_dept import StateDeptResult


@pytest.fixture
def _mock_cache():
    from unittest.mock import MagicMock
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    with patch("src.api.routers.advisories.get_cache", return_value=cache):
        yield cache


@pytest.fixture
def _state_dept_ok():
    result = StateDeptResult(
        advisory_level=2,
        title="Exercise Increased Caution",
        url="https://travel.state.gov/brazil",
        updated_at="2026-03-15",
    )
    with patch("src.api.routers.advisories.fetch_advisory", return_value=result):
        yield


@pytest.fixture
def _state_dept_none():
    with patch("src.api.routers.advisories.fetch_advisory", return_value=None):
        yield


@pytest.mark.asyncio
async def test_advisories_returns_200_for_valid_country(_mock_cache, _state_dept_ok):
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/advisories/BR")
    assert resp.status_code == 200
    body = resp.json()
    assert body["country_code"] == "BR"
    assert isinstance(body["advisories"], list)
    assert len(body["advisories"]) == 1
    assert body["advisories"][0]["level"] == 2


@pytest.mark.asyncio
async def test_advisories_returns_404_when_no_advisory(_mock_cache, _state_dept_none):
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/advisories/BR")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_advisories_returns_422_for_invalid_country_code():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/advisories/INVALID")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_advisories_returns_422_for_single_char():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/advisories/B")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_advisories_returns_cached_when_available(_mock_cache, _state_dept_ok):
    from src.main import app
    import json
    from datetime import datetime, timezone
    cached_data = {
        "country_code": "BR",
        "country_name": "Brazil",
        "advisories": [{"source": "U.S. State Department", "level": 2,
                        "title": "Cached", "updated_at": "2026-03-15", "url": "http://x"}],
        "data_sources": ["state_dept"],
        "cached": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _mock_cache.get = AsyncMock(return_value=cached_data)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/advisories/BR")
    assert resp.status_code == 200
    assert resp.json()["cached"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_routers/test_advisories.py -v
```

Expected: FAIL (stub router has no routes)

- [ ] **Step 3: Implement advisories router**

`src/api/routers/advisories.py`:
```python
import json
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from src.cache.cache_factory import get_cache
from src.models.advisory import Advisory, AdvisoryResponse
from src.models.countries import get_country_name
from src.services.state_dept import fetch_advisory

router = APIRouter()

CountryCode = Annotated[str, Path(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")]

_TTL = 6 * 3600  # 6 hours


@router.get("/{country_code}", response_model=AdvisoryResponse)
async def get_advisories(country_code: CountryCode) -> AdvisoryResponse:
    cache = get_cache()
    cache_key = f"advisories:{country_code}"

    cached = await cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return AdvisoryResponse(**cached)

    result = await fetch_advisory(country_code)
    if not result:
        raise HTTPException(status_code=404, detail=f"No advisories found for {country_code}")

    advisory = Advisory(
        source="U.S. State Department",
        level=result.advisory_level,
        title=result.title,
        updated_at=result.updated_at,
        url=result.url,
    )
    response = AdvisoryResponse(
        country_code=country_code,
        country_name=get_country_name(country_code),
        advisories=[advisory],
        data_sources=["state_dept"],
        cached=False,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    await cache.set(cache_key, response.model_dump(), ttl_seconds=_TTL)
    return response
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_routers/test_advisories.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/routers/advisories.py tests/test_routers/test_advisories.py
git commit -m "feat: advisories router with cache and 404 handling"
```

---

## Task 14: Risk Router + Tests

**Files:**
- Modify: `src/api/routers/risk.py`
- Create: `tests/test_routers/test_risk.py`

- [ ] **Step 1: Write failing tests**

`tests/test_routers/test_risk.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from src.services.state_dept import StateDeptResult
from src.collectors.weather import WeatherResult
from src.collectors.human_events import GdeltResult


def _make_mocks(state_dept=True, weather=True, gdelt=True, amadeus=False, acled=False):
    """Build patch context managers for all collectors."""
    sd = StateDeptResult(2, "Exercise Increased Caution", "http://x", "2026-03-15") if state_dept else None
    wt = WeatherResult(storm_severity=1.0, flood_severity=0.5) if weather else None
    gd = GdeltResult(civil_unrest_severity=2.0) if gdelt else None

    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    return (
        patch("src.api.routers.risk.fetch_advisory", return_value=sd),
        patch("src.api.routers.risk.fetch_weather_events", return_value=wt),
        patch("src.api.routers.risk.fetch_gdelt", return_value=gd),
        patch("src.api.routers.risk.fetch_acled", return_value=None),
        patch("src.api.routers.risk.fetch_geosure", return_value=None),
        patch("src.api.routers.risk.log_risk_event", new_callable=AsyncMock),
        patch("src.api.routers.risk.get_cache", return_value=cache),
    )


@pytest.mark.asyncio
async def test_risk_returns_200_full_response():
    from src.main import app
    patches = _make_mocks()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/risk/BR")
    assert resp.status_code == 200
    body = resp.json()
    assert body["country_code"] == "BR"
    assert 0 <= body["score"] <= 100
    assert body["risk_level"] in ("low", "medium", "high", "critical")
    assert body["score_confidence"] in ("full", "partial", "low")
    assert isinstance(body["data_sources"], list)
    assert isinstance(body["sources_unavailable"], list)
    assert "breakdown" in body


@pytest.mark.asyncio
async def test_risk_returns_200_with_partial_confidence_when_some_sources_fail():
    from src.main import app
    patches = _make_mocks(weather=False, gdelt=False)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/risk/BR")
    assert resp.status_code == 200
    assert resp.json()["score_confidence"] == "low"


@pytest.mark.asyncio
async def test_risk_returns_200_with_low_confidence_when_only_state_dept():
    from src.main import app
    patches = _make_mocks(weather=False, gdelt=False, state_dept=True)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/risk/BR")
    assert resp.status_code == 200
    assert resp.json()["score_confidence"] == "low"


@pytest.mark.asyncio
async def test_risk_returns_503_when_all_sources_fail():
    from src.main import app
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    with patch("src.api.routers.risk.fetch_advisory", return_value=None), \
         patch("src.api.routers.risk.fetch_weather_events", return_value=None), \
         patch("src.api.routers.risk.fetch_gdelt", return_value=None), \
         patch("src.api.routers.risk.fetch_acled", return_value=None), \
         patch("src.api.routers.risk.fetch_geosure", return_value=None), \
         patch("src.api.routers.risk.log_risk_event", new_callable=AsyncMock), \
         patch("src.api.routers.risk.get_cache", return_value=cache):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/risk/BR")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_risk_returns_422_for_invalid_country_code():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/risk/ZZZ")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_returns_422_for_numeric_code():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/risk/12")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_returns_422_for_single_char():
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/risk/B")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_returns_cached_result():
    from src.main import app
    from datetime import datetime, timezone
    cached_data = {
        "country_code": "BR",
        "country_name": "Brazil",
        "score": 48.0,
        "risk_level": "medium",
        "score_confidence": "partial",
        "breakdown": {},
        "advisories": [],
        "data_sources": ["state_dept"],
        "sources_unavailable": ["amadeus_geosure", "acled"],
        "cached": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    cache = MagicMock()
    cache.get = AsyncMock(return_value=cached_data)
    cache.set = AsyncMock()
    with patch("src.api.routers.risk.get_cache", return_value=cache), \
         patch("src.api.routers.risk.log_risk_event", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/risk/BR")
    assert resp.status_code == 200
    assert resp.json()["cached"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_routers/test_risk.py -v
```

Expected: FAIL (stub router has no routes)

- [ ] **Step 3: Implement risk router**

`src/api/routers/risk.py`:
```python
import asyncio
import time
import uuid
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from src.cache.cache_factory import get_cache
from src.collectors.human_events import fetch_gdelt, fetch_acled
from src.collectors.weather import fetch_weather_events
from src.logging.bigquery_logger import log_risk_event
from src.models.advisory import Advisory
from src.models.countries import get_country_name
from src.models.risk_score import RiskScore
from src.services.amadeus_client import fetch_geosure
from src.services.scorer import compute_score
from src.services.state_dept import fetch_advisory

router = APIRouter()

CountryCode = Annotated[str, Path(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")]

_RISK_TTL = 3600  # 1 hour


@router.get("/{country_code}", response_model=RiskScore)
async def get_risk(country_code: CountryCode) -> RiskScore:
    start = time.monotonic()
    request_id = str(uuid.uuid4())

    cache = get_cache()
    cache_key = f"risk:{country_code}"

    cached = await cache.get(cache_key)
    if cached:
        cached["cached"] = True
        asyncio.create_task(log_risk_event(
            request_id=request_id,
            country_code=country_code,
            score=cached["score"],
            risk_level=cached["risk_level"],
            score_confidence=cached["score_confidence"],
            data_sources=cached["data_sources"],
            sources_unavailable=cached["sources_unavailable"],
            breakdown=cached.get("breakdown", {}),
            cached=True,
            response_ms=int((time.monotonic() - start) * 1000),
        ))
        return RiskScore(**cached)

    # Parallel collection from all sources
    state_dept_res, weather_res, gdelt_res, geosure_res, acled_res = await asyncio.gather(
        fetch_advisory(country_code),
        fetch_weather_events(country_code),
        fetch_gdelt(country_code),
        fetch_geosure(country_code),
        fetch_acled(country_code),
        return_exceptions=False,
    )

    scored = compute_score(
        advisory_level=state_dept_res.advisory_level if state_dept_res else None,
        physical_safety=geosure_res.physical_safety if geosure_res else None,
        health_medical=geosure_res.health_medical if geosure_res else None,
        political_freedom=geosure_res.political_freedom if geosure_res else None,
        theft_risk=geosure_res.theft_risk if geosure_res else None,
        storm_severity=weather_res.storm_severity if weather_res else None,
        flood_severity=weather_res.flood_severity if weather_res else None,
        civil_unrest_severity=gdelt_res.civil_unrest_severity if gdelt_res else None,
        conflict_severity=acled_res.conflict_severity if acled_res else None,
    )

    if scored is None:
        raise HTTPException(status_code=503, detail="All data sources unavailable")

    advisories = []
    if state_dept_res:
        advisories.append(Advisory(
            source="U.S. State Department",
            level=state_dept_res.advisory_level,
            title=state_dept_res.title,
            updated_at=state_dept_res.updated_at,
            url=state_dept_res.url,
        ))

    response = RiskScore(
        country_code=country_code,
        country_name=get_country_name(country_code),
        score=scored["score"],
        risk_level=scored["risk_level"],
        score_confidence=scored["score_confidence"],
        breakdown=scored["breakdown"],
        advisories=advisories,
        data_sources=scored["data_sources"],
        sources_unavailable=scored["sources_unavailable"],
        cached=False,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    await cache.set(cache_key, response.model_dump(), ttl_seconds=_RISK_TTL)

    asyncio.create_task(log_risk_event(
        request_id=request_id,
        country_code=country_code,
        score=response.score,
        risk_level=response.risk_level.value,
        score_confidence=response.score_confidence.value,
        data_sources=response.data_sources,
        sources_unavailable=response.sources_unavailable,
        breakdown=response.breakdown.model_dump(),
        cached=False,
        response_ms=int((time.monotonic() - start) * 1000),
    ))

    return response
```

- [ ] **Step 4: Run all risk router tests**

```bash
uv run pytest tests/test_routers/test_risk.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Run all tests to verify nothing broken**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/api/routers/risk.py tests/test_routers/test_risk.py
git commit -m "feat: risk router with parallel collection, 503 and graceful degradation"
```

---

## Task 15: Dockerfile

**Files:**
- Create: `infra/Dockerfile`

- [ ] **Step 1: Create Dockerfile**

`infra/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

COPY src/ ./src/

ENV PORT=8080
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: Also create a root-level Dockerfile symlink for Cloud Build**

Cloud Build looks for `Dockerfile` at the repo root by default:

```bash
cp infra/Dockerfile Dockerfile
```

- [ ] **Step 3: Verify Docker build works locally**

```bash
docker build -t duty-of-care-api .
```

Expected: image built successfully.

- [ ] **Step 4: Test container locally**

```bash
docker run -p 8080:8080 --env-file .env duty-of-care-api
```

In another terminal:
```bash
curl http://localhost:8080/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 5: Commit**

```bash
git add Dockerfile infra/Dockerfile
git commit -m "feat: Dockerfile for Cloud Run deployment"
```

---

## Task 16: Cloud Build Pipeline

**Files:**
- Create: `infra/cloudbuild.yaml`
- Create root-level: `cloudbuild.yaml`

- [ ] **Step 1: Create cloudbuild.yaml**

`cloudbuild.yaml`:
```yaml
substitutions:
  _REGION: us-central1
  _SERVICE: duty-of-care-api
  _REPO: duty-of-care

steps:
  # Step 1: Run tests — gate before build
  - name: 'python:3.12-slim'
    id: 'test'
    entrypoint: bash
    args:
      - '-c'
      - |
        pip install uv -q &&
        uv sync -q &&
        uv run pytest tests/ -v --tb=short
    env:
      - 'CACHE_BACKEND=memory'
      - 'BQ_LOGGING_ENABLED=false'

  # Step 2: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build'
    waitFor: ['test']
    args:
      - 'build'
      - '-t'
      - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/${_SERVICE}:$COMMIT_SHA'
      - '.'

  # Step 3: Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    id: 'push'
    waitFor: ['build']
    args:
      - 'push'
      - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/${_SERVICE}:$COMMIT_SHA'

  # Step 4: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    id: 'deploy'
    waitFor: ['push']
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE}'
      - '--image=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/${_SERVICE}:$COMMIT_SHA'
      - '--region=${_REGION}'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-secrets=AMADEUS_CLIENT_ID=AMADEUS_CLIENT_ID:latest,AMADEUS_CLIENT_SECRET=AMADEUS_CLIENT_SECRET:latest,ACLED_API_KEY=ACLED_API_KEY:latest,ACLED_EMAIL=ACLED_EMAIL:latest'
      - '--set-env-vars=CACHE_BACKEND=firestore,BQ_LOGGING_ENABLED=true,GCP_PROJECT_ID=$PROJECT_ID'

images:
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/${_SERVICE}:$COMMIT_SHA'
```

- [ ] **Step 2: Copy to infra/**

```bash
cp cloudbuild.yaml infra/cloudbuild.yaml
```

- [ ] **Step 3: Commit**

```bash
git add cloudbuild.yaml infra/cloudbuild.yaml
git commit -m "feat: Cloud Build pipeline with test gate before deploy"
```

---

## Task 17: GCP Infrastructure Setup Script

**Files:**
- Create: `infra/setup.sh`

- [ ] **Step 1: Create setup script**

`infra/setup.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="duty-of-care-api"
REGION="us-central1"
REPO="duty-of-care"
GITHUB_OWNER="<YOUR_GITHUB_USERNAME>"
GITHUB_REPO="<YOUR_REPO_NAME>"

echo "==> Creating GCP project..."
gcloud projects create "$PROJECT_ID" --name="Duty of Care API" || echo "Project may already exist"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  bigquery.googleapis.com

echo "==> Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Duty of Care API images" || echo "Repo may already exist"

echo "==> Creating secrets in Secret Manager..."
echo "Enter AMADEUS_CLIENT_ID (press Enter to skip):"
read -r AMADEUS_CLIENT_ID
if [ -n "$AMADEUS_CLIENT_ID" ]; then
  echo -n "$AMADEUS_CLIENT_ID" | gcloud secrets create AMADEUS_CLIENT_ID --data-file=- || \
  echo -n "$AMADEUS_CLIENT_ID" | gcloud secrets versions add AMADEUS_CLIENT_ID --data-file=-
fi

echo "Enter AMADEUS_CLIENT_SECRET (press Enter to skip):"
read -r AMADEUS_CLIENT_SECRET
if [ -n "$AMADEUS_CLIENT_SECRET" ]; then
  echo -n "$AMADEUS_CLIENT_SECRET" | gcloud secrets create AMADEUS_CLIENT_SECRET --data-file=- || \
  echo -n "$AMADEUS_CLIENT_SECRET" | gcloud secrets versions add AMADEUS_CLIENT_SECRET --data-file=-
fi

echo "Enter ACLED_API_KEY (press Enter to skip):"
read -r ACLED_API_KEY
if [ -n "$ACLED_API_KEY" ]; then
  echo -n "$ACLED_API_KEY" | gcloud secrets create ACLED_API_KEY --data-file=- || \
  echo -n "$ACLED_API_KEY" | gcloud secrets versions add ACLED_API_KEY --data-file=-
fi

echo "Enter ACLED_EMAIL (press Enter to skip):"
read -r ACLED_EMAIL
if [ -n "$ACLED_EMAIL" ]; then
  echo -n "$ACLED_EMAIL" | gcloud secrets create ACLED_EMAIL --data-file=- || \
  echo -n "$ACLED_EMAIL" | gcloud secrets versions add ACLED_EMAIL --data-file=-
fi

echo "==> Creating Firestore database..."
gcloud firestore databases create --location=nam5 || echo "Firestore may already exist"

echo "==> Creating BigQuery dataset..."
bq mk --dataset "${PROJECT_ID}:duty_of_care" || echo "Dataset may already exist"

echo "==> Creating BigQuery table risk_events..."
bq mk --table \
  "${PROJECT_ID}:duty_of_care.risk_events" \
  request_id:STRING,country_code:STRING,score:FLOAT,risk_level:STRING,score_confidence:STRING,data_sources:STRING,sources_unavailable:STRING,breakdown:STRING,cached:BOOL,requested_at:TIMESTAMP,response_ms:INTEGER \
  || echo "Table may already exist"

echo "==> Setting IAM permissions for Cloud Build..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for ROLE in roles/run.admin roles/secretmanager.secretAccessor roles/artifactregistry.writer roles/bigquery.dataEditor roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA}" \
    --role="$ROLE"
done

echo "==> Creating Cloud Build trigger..."
gcloud builds triggers create github \
  --repo-name="$GITHUB_REPO" \
  --repo-owner="$GITHUB_OWNER" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --name="deploy-on-main"

echo ""
echo "==> Setup complete!"
echo "Next steps:"
echo "  1. Push your code to GitHub: git remote add origin <url> && git push -u origin main"
echo "  2. Connect your GitHub repo to Cloud Build in the GCP Console if not done already"
echo "  3. The pipeline will run automatically on every push to main"
echo "  4. Access Swagger UI at: https://${PROJECT_ID}-<hash>-uc.a.run.app/docs"
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x infra/setup.sh
git add infra/setup.sh
git commit -m "feat: GCP one-time setup script"
```

---

## Task 18: Final Check — Run Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS. Count should include:
- `tests/test_scorer.py` — 12 tests
- `tests/test_services.py` — ~14 tests
- `tests/test_routers/test_health.py` — 1 test
- `tests/test_routers/test_advisories.py` — 5 tests
- `tests/test_routers/test_risk.py` — 8 tests

- [ ] **Step 2: Verify local server starts**

```bash
uv run uvicorn src.main:app --reload --port 8000
```

In another terminal:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/risk/BR
curl http://localhost:8000/advisories/BR
```

- [ ] **Step 3: Test Docker container**

```bash
docker build -t duty-of-care-api .
docker run -p 8080:8080 --env-file .env duty-of-care-api &
curl http://localhost:8080/health
curl http://localhost:8080/risk/BR
```

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: final integration verification"
```

---

## Deployment Checklist

Before running `infra/setup.sh`:

- [ ] `gcloud` CLI installed and authenticated (`gcloud auth login`)
- [ ] Billing account linked to the GCP project (`gcloud billing accounts list`)
- [ ] GitHub repo created and code pushed to `main` branch
- [ ] GitHub connected to Cloud Build in GCP Console (Connections section)
- [ ] Replace `<YOUR_GITHUB_USERNAME>` and `<YOUR_REPO_NAME>` in `infra/setup.sh`

After running `infra/setup.sh`:

- [ ] Push to `main` triggers Cloud Build
- [ ] Cloud Build runs tests → build → push → deploy (all green)
- [ ] Cloud Run URL accessible: `https://<service>-<hash>-uc.a.run.app/health`
- [ ] Swagger UI: `https://<service>-<hash>-uc.a.run.app/docs`
- [ ] Test: `curl https://<url>/risk/BR` returns valid JSON with score
