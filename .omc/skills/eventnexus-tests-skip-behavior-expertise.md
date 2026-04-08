# eventnexus Backend: Testes de Integração Aparecem como SKIPPED sem PostgreSQL

## The Insight
Os testes de integração do `eventnexus` backend (`test_repository.py`, `test_routes.py`) usam `pytest.skip()` quando o PostgreSQL não está disponível — eles **não falham**, aparecem como **SKIPPED**. Isso é comportamento esperado, não um problema.

## Why This Matters
Ao rodar `pytest tests/` sem PostgreSQL rodando, você vê 15 testes SKIPPED e pode achar que algo está errado com o setup ou que os testes não existem. Na verdade, a suíte está funcionando corretamente — os testes unitários (normalization, scoring) rodam sempre; os de integração pulam graciosamente.

## Recognition Pattern
```
tests/test_repository.py::TestEventRepository::test_upsert_inserts_new_event SKIPPED
tests/test_routes.py::TestHealthRoute::test_health_returns_200 SKIPPED
...
15 skipped in 0.37s
```
Isso é OK. Não é falha.

## The Approach
Para rodar **todos** os testes (incluindo integração):
```bash
# Subir PostgreSQL via Docker:
docker compose up -d db
# Aguardar ~3s e rodar:
cd eventnexus && .venv/bin/python -m pytest tests/ -v
```
Esperado: 28 passed.

Para rodar apenas **testes unitários** (sem banco):
```bash
.venv/bin/python -m pytest tests/test_normalization.py tests/test_scoring.py -v
```
Esperado: 13 passed.

## Files
- `eventnexus/tests/conftest.py` — `pytest.skip("PostgreSQL not available")` no fixture `create_test_db`
- `eventnexus/docker-compose.yml` — sobe o PostgreSQL local para testes
