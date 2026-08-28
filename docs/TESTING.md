# Testing methodology

Assignment Question 2 asks you to **explain test cases built to assure quality**.  
Tests mirror **production behavior** — same routes, JWT, SSE contract, Postgres persistence, rate-limit code path.

## Pyramid

```
        E2E          live HTTP — register → chat → stream
       /   \
  Integration    full API + Postgres (docker)
     /     \
   Unit          ai/chat routing, LLM helpers, rate limit, DTOs
```

## Chat coverage (production-aligned)

| Scenario | Layer | Test |
| --- | --- | --- |
| JWT required on `/chat/*` | Integration | `test_chat_complete_without_token_returns_401` |
| Blank message → 422 | Integration | `test_chat_complete_blank_message_returns_422` |
| Complete persists user + assistant | Integration | `test_chat_complete_persists_conversation` |
| Multi-turn same `conversation_id` | Integration + E2E | `test_chat_multi_turn_same_conversation_id` |
| Unknown / other user's thread → 404 | Integration | `test_chat_unknown_conversation_id_returns_404` |
| `use_rag` with no documents | Integration | `test_chat_use_rag_without_documents_still_succeeds` |
| SSE `meta` → `token` → `done` | Integration + E2E | `test_chat_stream_emits_meta_token_done` |
| SSE error on bad conversation | Integration | `test_chat_stream_unknown_conversation_emits_error_event` |
| Rate limit → 429 | Unit + Integration | `test_rate_limit_*`, `test_chat_rate_limit_returns_429` |
| RAG route when chunks found | Unit | `test_optional_rag_uses_rag_route_when_context_found` |
| RAG fail-soft on retriever error | Unit | `test_optional_rag_fail_soft_on_retriever_error` |
| Cookie session auth | Integration | `test_session_auth.py` |
| Stable error messages | Unit | `test_errors_envelope.py` |

## Commands

```powershell
cd backend
docker compose up -d --build

# All
docker compose run --rm api pytest

# Unit only — no Postgres
docker compose run --rm api pytest -m unit

# Integration — chat + auth + knowledge
docker compose run --rm api pytest -m integration

# E2E — running API
docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e
```

## Unit tests (`pytest -m unit`)

**No Docker. No Postgres.**

| Area | File |
| --- | --- |
| Security | `tests/services/test_security.py` |
| Rate limit logic | `tests/services/test_rate_limit.py` |
| DTOs / errors | `tests/api/test_errors.py` |
| Mapping | `tests/api/test_mapping.py` |
| Routes | `tests/api/test_router.py` |
| Chat AI flow | `tests/ai/test_chat.py` |
| LLM helpers | `tests/ai/test_llm_providers.py` |
| Retriever (mocked) | `tests/ai/test_retrieve_unit.py` |
| Prompts / chunker | `tests/ai/test_prompts.py` |

## Integration tests (`pytest -m integration`)

Uses `httpx.AsyncClient` + real Postgres. Fixture `auth_user` = register per test (isolation).

| File | Focus |
| --- | --- |
| `test_health.py` | Public health |
| `test_auth_api.py` | Register, login, 401 |
| `test_chat_api.py` | **Full chat production paths** |
| `test_knowledge_api.py` | Documents + RAG chat |

## E2E tests (`pytest -m e2e`)

Hits the same URLs as Next.js (`E2E_BASE_URL`).

## Production patterns used

- **Fixtures** — `auth_user`, `api_client`, `fake_redis` (rate limit without real Redis)
- **Helpers** — `chat_complete()`, `chat_stream_events()` (DRY, same as UI calls)
- **Isolation** — unique email per test; no shared conversation state
- **Assert contracts** — SSE event order, error codes (`UNAUTHORIZED`, `NOT_FOUND`, `RATE_LIMITED`)
- **Fail-soft paths** — retriever errors tested at unit layer

## Not automated (manual demo)

- Browser UI clicks
- Real Gemini/OpenAI answer quality
- ARQ summarize after 4 messages

Presentation: [PRESENTATION.md](PRESENTATION.md)
