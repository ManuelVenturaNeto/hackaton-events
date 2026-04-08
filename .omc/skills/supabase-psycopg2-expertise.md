# Supabase + psycopg2: Três Gotchas de Conexão

## The Insight
A connection string do Supabase tem três problemas incompatíveis com psycopg2 que aparecem em sequência: parâmetro `pgbouncer=true` inválido, senha com `/` quebrando o parsing da URL, e conexão travada em transação abortada após falha em background task.

## Why This Matters
Sem esse conhecimento você gasta tempo em três erros distintos que parecem não relacionados:
1. `invalid URI query parameter: "pgbouncer"` — psycopg2 não aceita esse parâmetro
2. `invalid integer value "Um*3z" for connection option "port"` — `/` na senha quebra o parsing
3. `InFailedSqlTransaction: current transaction is aborted` — a conexão compartilhada fica suja após uma exceção no sync em background

## Recognition Pattern
- Stack: FastAPI + psycopg2 + Supabase pooler (pgBouncer)
- Erro 1: `ProgrammingError: invalid URI query parameter: "pgbouncer"`
- Erro 2: `OperationalError: invalid integer value ... for connection option "port"`
- Erro 3: `InFailedSqlTransaction: commands ignored until end of transaction block`

## The Approach

**Fix 1 — Strip `pgbouncer=true` da URL antes de conectar:**
```python
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def _clean_url(url: str) -> str:
    parsed = urlparse(url)
    params = {k: v for k, v in parse_qs(parsed.query).items() if k != "pgbouncer"}
    cleaned = parsed._replace(query=urlencode({k: v[0] for k, v in params.items()}))
    return urlunparse(cleaned)
```

**Fix 2 — URL-encode a senha antes de colocar no `.env`:**
```python
from urllib.parse import quote_plus
print(quote_plus("Um*3z/*fhsC4nJR"))  # → Um%2A3z%2F%2AfhsC4nJR
```
Caracteres problemáticos: `/` → `%2F`, `*` → `%2A`, `@` → `%40`, `#` → `%23`

**Fix 3 — Rollback automático em `get_connection()` quando a transação falhou:**
```python
import psycopg2.extensions

def get_connection(self):
    if self._conn is None or self._conn.closed:
        self._conn = psycopg2.connect(self._clean_url(self.database_url), ...)
        self._conn.autocommit = False
    elif self._conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
        try:
            self._conn.rollback()
        except Exception:
            self._conn = psycopg2.connect(self._clean_url(self.database_url), ...)
            self._conn.autocommit = False
    return self._conn
```

**Fix 4 — `extra="ignore"` no Settings para variáveis extras no .env (ex: DIRECT_URL):**
```python
model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

## Files
- `eventnexus/app/database.py` — fixes 1 e 3
- `eventnexus/app/config.py` — fix 4
- `eventnexus/.env` — fix 2 (senha URL-encoded)
