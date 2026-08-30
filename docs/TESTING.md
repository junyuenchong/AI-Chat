# Testing methodology

Tests mirror **production behavior** — same routes, JWT/cookie auth, SSE contract, Postgres persistence, rate-limit code path.

---

## Tooling overview

| Layer | Test | Format / lint | Type check |
| --- | --- | --- | --- |
| **Backend** | pytest, pytest-asyncio, httpx | Ruff (`pyproject.toml`) | type hints + Pylance |
| **Frontend** | Jest, React Testing Library, Playwright | ESLint + Prettier | TypeScript (`tsconfig.json`) |

Details: [../backend/README.md](../backend/README.md#tooling) · [../frontend/README.md](../frontend/README.md#tooling)

---

## Pyramid

```
        E2E          live HTTP — register → chat → stream
       /   \
  Integration    full API + Postgres (Docker)
     /     \
   Unit          mappers, RAG routing, LLM helpers, rate limit, DTOs
```

---

## Backend commands

Run from `backend/`.

```powershell
docker compose up -d --build

docker compose run --rm api pytest
docker compose run --rm api pytest -m unit
docker compose run --rm api pytest -m integration
docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e
.\scripts\ruff.ps1
```

### Migrations & seeds (test setup)

| Action | Docker |
| --- | --- |
| Apply migrations | `docker compose run --rm api alembic upgrade head` |
| Seed demo data | `docker compose run --rm api python alembic/seeds/run.py` |
| Reset DB | `docker compose down -v` then migrate + seed again |

---

## Frontend commands

Run from `frontend/`.

```powershell
npm run typecheck
npm run lint
npm run format:check
npm test
npm run test:e2e
```

| Action | Command |
| --- | --- |
| TypeScript | `npm run typecheck` |
| ESLint | `npm run lint` |
| Prettier check | `npm run format:check` |
| Jest (all) | `npm test` |
| Jest unit | `npm run test:unit` |
| Jest components | `npm run test:components` |
| Jest integration | `npm run test:integration` |
| Playwright e2e | `npm run test:e2e` |

---

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
| LLM retry on transient error | Unit | `test_llm_retry.py` |
| Retry helper (backoff, non-retryable) | Unit | `test_retry.py` |
| Cookie session auth | Integration | `test_session_auth.py` |
| Stable error messages | Unit | `test_errors_envelope.py` |
| DTO / mapper layer | Unit | `test_mapping.py` (AuthMapper, DocumentsMapper) |

---

## Backend unit tests (`pytest -m unit`)

**No Docker. No Postgres.**

| Area | File |
| --- | --- |
| Security | `tests/unit/services/test_security.py` |
| Rate limit logic | `tests/unit/services/test_rate_limit.py` |
| DTOs / errors | `tests/unit/api/test_errors.py` |
| Error envelope | `tests/unit/api/test_errors_envelope.py` |
| Mappers | `tests/unit/api/test_mapping.py` |
| Routes | `tests/unit/api/test_router.py` |
| Chat AI flow | `tests/unit/ai/test_chat.py` |
| LLM retry + failover | `tests/unit/ai/test_llm_retry.py` |
| LLM helpers | `tests/unit/ai/test_llm_providers.py` |
| Retriever (mocked) | `tests/unit/ai/test_retrieve_unit.py` |
| Prompts | `tests/unit/ai/test_prompts.py` |
| Retry helpers | `tests/unit/shared/test_retry.py` |

---

## Backend integration tests (`pytest -m integration`)

Uses `httpx.AsyncClient` + real Postgres. Fixture `auth_user` = register per test (isolation).

| File | Focus |
| --- | --- |
| `test_health.py` | Public health |
| `test_auth_api.py` | Register, login, 401 |
| `test_session_auth.py` | Cookie session auth |
| `test_chat_api.py` | Full chat production paths |
| `test_knowledge_api.py` | Documents + RAG chat |

---

## Backend E2E tests (`pytest -m e2e`)

Hits the same URLs as Next.js (`E2E_BASE_URL`).

| File | Focus |
| --- | --- |
| `test_smoke.py` | Register → chat → stream smoke |

---

## Frontend tests

### Jest

| Area | Folder |
| --- | --- |
| API clients | `tests/unit/features/*/api.test.ts` |
| Hooks | `tests/unit/features/*/hooks.test.tsx` |
| SSE reader | `tests/unit/lib/sse/reader.test.ts` |
| Components | `tests/components/` |
| Integration | `tests/integration/` |

### Playwright

| File | Focus |
| --- | --- |
| `tests/e2e/auth.spec.ts` | Login / register |
| `tests/e2e/chat.spec.ts` | Chat UI |
| `tests/e2e/knowledge.spec.ts` | Document upload |

Requires backend at `http://localhost:8000`.

---

## Production patterns used

- **Fixtures** — `auth_user`, `api_client`, `fake_redis` (rate limit without real Redis)
- **Helpers** — `chat_complete()`, `chat_stream_events()` (same shapes as UI calls)
- **Isolation** — unique email per test; no shared conversation state
- **Assert contracts** — SSE event order, error codes (`UNAUTHORIZED`, `NOT_FOUND`, `RATE_LIMITED`)
- **Fail-soft paths** — retriever errors tested at unit layer

### Infrastructure under test

| Concern | Module | How tests cover it |
| --- | --- | --- |
| Sessions | `infrastructure/cache/redis.py` | `fake_redis` patches `get_redis` |
| Rate limits | `core/middleware.py` + cache | Unit logic + integration 429 |
| Vector search | `infrastructure/ai/langchain/retrieval.py` + `infrastructure/vector/pgvector.py` | Retriever unit tests (mocked DB) |
| LLM retry / failover | `shared/retry.py` + `infrastructure/ai/langchain/llm.py` | `test_retry.py`, `test_llm_retry.py` |
| Background jobs | `infrastructure/messaging/` | ARQ `max_tries=3`; manual demo for worker |

---

## Not automated (manual demo)

- Real Gemini/OpenAI answer quality
- ARQ summarize after 4 messages (`messaging/tasks/cleanup.py`) — worker retries up to 3 times
- Document embedding worker (`messaging/tasks/document.py`) — worker retries up to 3 times

---

## Related docs

| Document | Purpose |
| --- | --- |
| [PRESENTATION.md](PRESENTATION.md) | Demo script |
| [SECURITY.md](SECURITY.md) | Auth and rate limits |
| [../README.md](../README.md) | Project overview |
| [../backend/README.md](../backend/README.md) | Backend tooling |
| [../frontend/README.md](../frontend/README.md) | Frontend tooling |
