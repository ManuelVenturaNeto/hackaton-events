# eventnexus Backend: Conexão Única Compartilhada — Limitação Arquitetural

## The Insight
O `Database` em `eventnexus/app/database.py` usa uma única conexão psycopg2 (`self._conn`) compartilhada por toda a aplicação FastAPI. Isso funciona para o hackathon, mas tem duas consequências não-óbvias:

1. **BackgroundTasks + exceção = conexão travada:** Se o sync em background lançar uma exceção no meio de uma query, a conexão fica em estado `STATUS_IN_TRANSACTION` abortado. Qualquer request subsequente falhará com `InFailedSqlTransaction` até que haja um rollback explícito.

2. **Requests concorrentes compartilham estado de transação:** Em produção sob carga, dois requests simultâneos podem corromper a transação um do outro, pois usam o mesmo `self._conn`.

## Why This Matters
Sem saber disso, você vê `InFailedSqlTransaction` em requests aparentemente não relacionados e não entende por quê — o sync falhou mas o GET /events também falha.

## Recognition Pattern
- `GET /api/events` retorna 500 após um `POST /api/events/sync` que falhou
- Log mostra: `psycopg2.errors.InFailedSqlTransaction: current transaction is aborted`
- Não há erro aparente no próprio GET /events

## The Approach

**Mitigação implementada** (suficiente para hackathon):
```python
elif self._conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
    try:
        self._conn.rollback()
    except Exception:
        self._conn = psycopg2.connect(...)  # reconecta se rollback falhar
```

**Fix correto para produção:** usar `psycopg2.pool.SimpleConnectionPool` ou `psycopg2.pool.ThreadedConnectionPool` em vez de conexão única. Cada request pegaria uma conexão do pool e devolveria ao finalizar.

## Files
- `eventnexus/app/database.py` — onde a mitigação foi implementada
