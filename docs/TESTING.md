# Testing methodology

Tests mirror **production behavior** — same routes, JWT auth, SSE contract, Postgres persistence.

Pytest **forces demo mode** (`tests/conftest.py` clears `GEMINI_API_KEY` and `OPENAI_API_KEY`) so all **51 backend tests** run without external API calls.

Frontend: **41 Jest tests** (unit, component, integration).

---

## Pyramid

```
        E2E          register → chat → stream
       /   \
  Integration    API + Postgres (Docker)
     /     \
   Unit          chat chain, messages, LLM retry, DTOs, JWT
```

---

## Backend commands

```powershell
cd backend
docker compose run --rm api pytest                              # all (51)
docker compose run --rm api pytest -m unit                      # unit only
docker compose run --rm api pytest -m integration               # integration
docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e
```

Requires Postgres running (`docker compose up postgres -d` or full stack).

---

## Backend coverage

### Chat

| Scenario | Layer | Test |
| --- | --- | --- |
| JWT required on `/chat/*` | Integration | `test_chat_complete_without_token_returns_401` |
| Blank message → 422 | Integration | `test_chat_complete_blank_message_returns_422` |
| Complete persists messages | Integration | `test_chat_complete_persists_conversation` |
| Multi-turn memory | Integration | `test_chat_multi_turn_same_conversation_id` |
| SSE `meta` → `token` → `done` | Integration + E2E | `test_chat_stream_emits_meta_token_done` |
| Unknown conversation → 404 | Integration | `test_chat_unknown_conversation_id_returns_404` |
| SSE error for missing thread | Integration | `test_chat_stream_unknown_conversation_emits_error_event` |

### LangChain / LLM

| Scenario | Layer | Test |
| --- | --- | --- |
| Message building | Unit | `test_chat.py` |
| `to_lc_messages` mapping | Unit | `test_llm_providers.py` |
| Demo mode reply | Unit | `test_demo_reply_mentions_demo_mode` |
| LLM retry / failover | Unit | `test_llm_retry.py` |
| System prompt | Unit | `test_prompts.py` |

### Auth & API

| Scenario | Layer | Test |
| --- | --- | --- |
| JWT register / login | Integration | `test_session_auth.py` |
| Route registration | Unit | `test_router.py` |
| Error envelope | Unit | `test_errors.py`, `test_errors_envelope.py` |
| Health check | Integration | `test_health.py` |
| Register → chat smoke | E2E | `test_live_register_chat_flow` |
| SSE contract | E2E | `test_live_chat_stream_contract` |

---

## Frontend commands

```powershell
cd frontend
npm test                    # 41 tests
npm run test:unit
npm run test:integration
npm run test:e2e            # Playwright — needs backend
```

| Spec / file | Focus |
| --- | --- |
| `tests/e2e/auth.spec.ts` | Login / register |
| `tests/e2e/chat.spec.ts` | Chat UI |
| `tests/unit/lib/api/client.test.ts` | API client, Bearer headers |
| `tests/unit/lib/sse/reader.test.ts` | SSE frame parsing |
| `tests/unit/features/auth/api.test.ts` | Auth API, token storage |
| `tests/unit/features/chat/api.test.ts` | Stream chat fetch |
| `tests/unit/features/chat/hooks.test.tsx` | `useChat` streaming |
| `tests/unit/features/health/hooks.test.tsx` | Health pills |
| `tests/integration/chat-stream.integration.test.tsx` | End-to-end SSE in Jest |
| `tests/components/AuthForm.test.tsx` | Login form |
| `tests/components/chat-ui.test.tsx` | Message list / input |

E2E requires backend at `http://localhost:8000`.

---

## What is NOT tested (by design)

- Live Gemini / OpenAI API calls in pytest (demo mode forced)
- RAG, embeddings, vector search (removed from Q2 scope)
- Redis, worker, cookie sessions (removed from Q2 scope)

---

## Related docs

[PRESENTATION.md](PRESENTATION.md) · [SECURITY.md](SECURITY.md) · [../README.md](../README.md) · [../backend/README.md](../backend/README.md) · [../frontend/README.md](../frontend/README.md)
