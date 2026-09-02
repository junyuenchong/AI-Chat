# Testing methodology

Tests mirror **production behavior** — same routes, JWT auth, SSE contract, Postgres persistence.

| Suite | Count | Runner | Needs |
| --- | --- | --- | --- |
| **Backend** | **51** | pytest | Docker + Postgres |
| **Frontend** | **41** | Jest | Node only |
| **Frontend E2E** | **5** | Playwright | Backend at `:8000` |

Pytest **forces demo mode** (`tests/conftest.py` clears `GEMINI_API_KEY` and `OPENAI_API_KEY`) — no live Gemini/OpenAI calls.

Markers are applied automatically by folder: `tests/unit/` → `unit`, `tests/integration/` → `integration`, `tests/e2e/` → `e2e`.

---

## Pyramid

```
        E2E (3 backend + 5 Playwright)     register → chat → stream
       /   \
  Integration (16)                         API + Postgres (Docker)
     /     \
   Unit (32)                                chat chain, retry, JWT, DTOs
```

---

## How to run

### Backend

```powershell
cd backend
docker compose up postgres -d          # or full stack
docker compose run --rm api pytest                              # all (51)
docker compose run --rm api pytest -m unit                      # unit only (32)
docker compose run --rm api pytest -m integration               # integration (16)
docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e   # e2e (3)
```

### Frontend

```powershell
cd frontend
npm test                    # 41 Jest tests
npm run test:unit           # unit only
npm run test:integration    # integration only
npm run test:e2e            # 5 Playwright tests — backend must be running
```

---

## Backend tests (51)

### Unit — AI / LangChain (12)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_build_llm_messages_includes_system_history_and_user` | `unit/ai/test_chat.py` | ChatChain builds system + history + user messages |
| `test_generate_full_reply_returns_answer` | `unit/ai/test_chat.py` | Non-streaming `generate_full_reply` returns answer dict |
| `test_stream_yields_tokens` | `unit/ai/test_chat.py` | Streaming yields token events from demo LLM |
| `test_streaming_maps_llm_provider_error_to_error_event` | `unit/ai/test_chat.py` | LLM failure during stream → `error` event |
| `test_complete_maps_llm_provider_error_to_domain_error` | `unit/ai/test_chat.py` | LLM failure on complete → `LLMError` |
| `test_to_lc_messages_includes_system_and_user` | `unit/ai/test_llm_providers.py` | Message mapper includes system prompt and user turn |
| `test_to_lc_messages_limits_history_window` | `unit/ai/test_llm_providers.py` | History is trimmed to configured window |
| `test_demo_reply_mentions_demo_mode` | `unit/ai/test_llm_providers.py` | Demo LLM response mentions demo mode |
| `test_demo_reply_echoes_user_message` | `unit/ai/test_llm_providers.py` | Demo LLM echoes user input |
| `test_complete_retries_transient_error_before_success` | `unit/ai/test_llm_retry.py` | Retries 429/503 before succeeding |
| `test_complete_fails_over_to_next_model_after_retries` | `unit/ai/test_llm_retry.py` | Falls back to secondary model after retries |
| `test_system_prompt_is_non_empty` | `unit/ai/test_prompts.py` | `SYSTEM_PROMPT` is defined and non-empty |

### Unit — API / DTOs (11)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_auth_mapper_hashes_password_and_lowercases_email` | `unit/api/test_mapping.py` | Register mapper hashes password, lowercases email |
| `test_auth_token_response_never_includes_hash` | `unit/api/test_mapping.py` | Token response has no password hash |
| `test_missing_login_fields_become_field_errors` | `unit/api/test_errors.py` | Missing login fields → validation field errors |
| `test_unknown_login_field_is_rejected` | `unit/api/test_errors.py` | Unknown JSON fields on login are rejected |
| `test_register_requires_all_fields` | `unit/api/test_errors.py` | Register requires email, password, name |
| `test_blank_chat_message_is_rejected` | `unit/api/test_errors.py` | Empty chat message → 422 |
| `test_request_validation_error_uses_same_formatter` | `unit/api/test_errors.py` | All validation errors use same envelope |
| `test_error_body_never_returns_empty_message` | `unit/api/test_errors_envelope.py` | Error responses always have a message |
| `test_field_errors_use_required_message_for_missing` | `unit/api/test_errors_envelope.py` | Missing fields get readable messages |
| `test_v1_routes_are_mounted` | `unit/api/test_router.py` | Auth, chat, conversations, health routes exist |
| `test_app_uses_v1_prefix` | `unit/api/test_router.py` | All routes under `/api/v1` |

### Unit — Security (4)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_password_hash_roundtrip` | `unit/services/test_security.py` | bcrypt hash + verify works |
| `test_corrupt_password_hash_is_rejected` | `unit/services/test_security.py` | Bad hash returns False, not 500 |
| `test_jwt_roundtrip` | `unit/services/test_security.py` | Create + decode JWT returns user id |
| `test_invalid_token_raises_value_error` | `unit/services/test_security.py` | Expired/invalid JWT raises ValueError |

### Unit — Retry (5)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_is_retryable_error_detects_transient_failures` | `unit/shared/test_retry.py` | 429, 503, timeout are retryable |
| `test_is_retryable_error_rejects_permanent_failures` | `unit/shared/test_retry.py` | 400, 401 are not retryable |
| `test_backoff_delay_grows_with_attempt` | `unit/shared/test_retry.py` | Exponential backoff increases per attempt |
| `test_retry_async_succeeds_after_transient_failure` | `unit/shared/test_retry.py` | Async retry succeeds after transient error |
| `test_retry_async_does_not_retry_permanent_failure` | `unit/shared/test_retry.py` | Permanent errors fail immediately |

### Integration — Auth (5)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_register_returns_bearer_token` | `integration/test_session_auth.py` | Register returns JWT access token |
| `test_me_requires_bearer_token` | `integration/test_session_auth.py` | `GET /auth/me` without token → 401 |
| `test_register_login_and_me` | `integration/test_auth_api.py` | Full flow: register → login → `/auth/me` |
| `test_duplicate_register_returns_conflict` | `integration/test_auth_api.py` | Duplicate email → 409 conflict |
| `test_protected_route_without_token_returns_401` | `integration/test_auth_api.py` | Protected route rejects missing JWT |

### Integration — Chat (10)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_chat_complete_without_token_returns_401` | `integration/test_chat_api.py` | `POST /chat/complete` requires JWT |
| `test_chat_stream_without_token_returns_401` | `integration/test_chat_api.py` | `POST /chat/stream` requires JWT |
| `test_chat_complete_blank_message_returns_422` | `integration/test_chat_api.py` | Blank message → validation error |
| `test_chat_complete_persists_conversation` | `integration/test_chat_api.py` | Reply saved to Postgres |
| `test_chat_multi_turn_same_conversation_id` | `integration/test_chat_api.py` | Follow-up uses same thread + history |
| `test_chat_unknown_conversation_id_returns_404` | `integration/test_chat_api.py` | Invalid thread id → 404 |
| `test_chat_other_users_conversation_returns_404` | `integration/test_chat_api.py` | Cannot access another user's thread |
| `test_chat_complete_returns_reply` | `integration/test_chat_api.py` | JSON complete returns content + conversation_id |
| `test_chat_stream_emits_meta_token_done` | `integration/test_chat_api.py` | SSE emits `meta` → `token` → `done` |
| `test_chat_stream_unknown_conversation_emits_error_event` | `integration/test_chat_api.py` | Bad thread id → SSE `error` event |

### Integration — Health (1)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_health_returns_dependency_flags` | `integration/test_health.py` | `GET /health` returns `postgres`, `llm`, `status` |

### E2E — Smoke (3)

| Test | File | What it verifies |
| --- | --- | --- |
| `test_live_health` | `e2e/test_smoke.py` | Health endpoint responds OK |
| `test_live_register_chat_flow` | `e2e/test_smoke.py` | Register → send message → get reply |
| `test_live_chat_stream_contract` | `e2e/test_smoke.py` | SSE stream follows `meta`/`token`/`done` contract |

---

## Frontend tests (41 Jest + 5 Playwright)

### Unit — API client (8)

| Test | File | What it verifies |
| --- | --- | --- |
| `returns path only in browser context` | `unit/lib/api/client.test.ts` | `apiUrl` uses same-origin in browser |
| `streamUrl delegates to apiUrl` | `unit/lib/api/client.test.ts` | SSE uses same URL builder |
| `returns message and field errors` | `unit/lib/api/client.test.ts` | `formatApiError` parses FastAPI envelope |
| `falls back when payload has no error object` | `unit/lib/api/client.test.ts` | Missing error object uses fallback |
| `includes Authorization when token is provided` | `unit/lib/api/client.test.ts` | `authHeaders` adds Bearer token |
| `returns parsed JSON on success` | `unit/lib/api/client.test.ts` | `apiJson` parses 200 response |
| `throws readable error on failure` | `unit/lib/api/client.test.ts` | Non-OK status throws Error with message |
| `includes status when body is not JSON` | `unit/lib/api/client.test.ts` | Non-JSON error includes HTTP status |

### Unit — SSE reader (2)

| Test | File | What it verifies |
| --- | --- | --- |
| `emits parsed events in order` | `unit/lib/sse/reader.test.ts` | `readSse` parses `event:` + `data:` frames |
| `throws when response has no body` | `unit/lib/sse/reader.test.ts` | Missing body throws clear error |

### Unit — Auth API (6)

| Test | File | What it verifies |
| --- | --- | --- |
| `registerUser posts credentials` | `unit/features/auth/api.test.ts` | Register POST + saves JWT to sessionStorage |
| `loginUser posts email and password` | `unit/features/auth/api.test.ts` | Login POST + saves JWT |
| `fetchCurrentUser returns null when no token is stored` | `unit/features/auth/api.test.ts` | Skips `/auth/me` when logged out |
| `fetchCurrentUser calls GET /auth/me when token exists` | `unit/features/auth/api.test.ts` | Restores session on page load |
| `fetchCurrentUser clears token on 401` | `unit/features/auth/api.test.ts` | Stale token cleared on 401 |
| `logoutUser clears stored token` | `unit/features/auth/api.test.ts` | Logout removes JWT from sessionStorage |

### Unit — Auth hooks (3)

| Test | File | What it verifies |
| --- | --- | --- |
| `calls login on submit in login mode` | `unit/features/auth/hooks.test.tsx` | `useAuthForm` calls login |
| `calls register on submit in register mode` | `unit/features/auth/hooks.test.tsx` | `useAuthForm` calls register |
| `surfaces local error when login throws` | `unit/features/auth/hooks.test.tsx` | Login failure shows error message |

### Unit — Chat API (2)

| Test | File | What it verifies |
| --- | --- | --- |
| `forwards SSE events on success` | `unit/features/chat/api.test.ts` | `streamChat` forwards parsed events |
| `emits error event when HTTP status is not OK` | `unit/features/chat/api.test.ts` | HTTP error → SSE-style error event |

### Unit — Chat hooks (2)

| Test | File | What it verifies |
| --- | --- | --- |
| `appends user and assistant messages after send` | `unit/features/chat/hooks.test.tsx` | `useChat` adds bubbles on send |
| `does not send when input is blank` | `unit/features/chat/hooks.test.tsx` | Empty input is ignored |

### Unit — Chat utils (4)

| Test | File | What it verifies |
| --- | --- | --- |
| `sets scrollTop to scrollHeight` | `unit/features/chat/utils.test.ts` | `scrollToBottom` scrolls message list |
| `does nothing when container is null` | `unit/features/chat/utils.test.ts` | Null container is safe |
| `prompts sign-in when logged out` | `unit/features/chat/utils.test.ts` | `welcomeMessage(false)` text |
| `shows new chat hint when logged in` | `unit/features/chat/utils.test.ts` | `welcomeMessage(true)` text |

### Unit — Conversations hooks (3)

| Test | File | What it verifies |
| --- | --- | --- |
| `opens conversation and returns message bubbles` | `unit/features/conversations/hooks.test.tsx` | `openConversation` loads messages |
| `resets state when starting a new chat` | `unit/features/conversations/hooks.test.tsx` | `startNewChat` clears active thread |
| `refreshes conversation list from API` | `unit/features/conversations/hooks.test.tsx` | `refresh` reloads sidebar list |

### Unit — Health hooks (2)

| Test | File | What it verifies |
| --- | --- | --- |
| `loads health status on mount` | `unit/features/health/hooks.test.tsx` | `useHealth` fetches on mount |
| `sets health to null when API fails` | `unit/features/health/hooks.test.tsx` | Failed health check → null state |

### Component (7)

| Test | File | What it verifies |
| --- | --- | --- |
| `renders login title and submit button` | `components/AuthForm.test.tsx` | Login form UI |
| `renders register title` | `components/AuthForm.test.tsx` | Register form UI |
| `calls submit when form is submitted` | `components/AuthForm.test.tsx` | Form submit handler fires |
| `renders user and assistant messages` | `components/chat-ui.test.tsx` | MessageList renders bubbles |
| `shows typing indicator on empty streaming assistant bubble` | `components/chat-ui.test.tsx` | "Thinking…" while streaming |
| `disables send when streaming` | `components/chat-ui.test.tsx` | Send button disabled during stream |
| `calls onSubmit when form is submitted` | `components/chat-ui.test.tsx` | ChatInput submit works |

### Integration — SSE (2)

| Test | File | What it verifies |
| --- | --- | --- |
| `accumulates streamed tokens into assistant bubble` | `integration/chat-stream.integration.test.tsx` | `useChat` accumulates tokens live |
| `readSse parses mock response end-to-end` | `integration/chat-stream.integration.test.tsx` | Full SSE parse + callback chain |

### E2E — Playwright (5)

| Test | File | What it verifies |
| --- | --- | --- |
| `user can register and reach the chat dashboard` | `e2e/auth.spec.ts` | Register flow in browser |
| `user can log out and return to login` | `e2e/auth.spec.ts` | Logout redirects to login |
| `existing user can sign in from login page` | `e2e/auth.spec.ts` | Login with demo credentials |
| `user can send a message and see assistant reply` | `e2e/chat.spec.ts` | Send message, see streamed reply |
| `new chat button resets the conversation pane` | `e2e/chat.spec.ts` | New chat clears active thread |

---

## What is NOT tested (by design)

| Area | Reason |
| --- | --- |
| Live Gemini / OpenAI API calls | Demo mode forced in pytest — no external network |
| RAG, embeddings, vector search | Removed from Q2 scope |
| Redis, worker, cookie sessions | Removed from Q2 scope |
| `DELETE /conversations/{id}` | Route exists; no dedicated test yet |
| Next.js proxy route (`app/api/v1/[...path]`) | Covered indirectly via client + integration tests |

---

## Related docs

[PRESENTATION.md](PRESENTATION.md) · [SECURITY.md](SECURITY.md) · [../README.md](../README.md) · [../backend/README.md](../backend/README.md) · [../frontend/README.md](../frontend/README.md)
