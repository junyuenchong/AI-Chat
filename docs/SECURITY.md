# Security & performance

Production-oriented auth, rate limiting, errors, and database tuning.

---

## Auth: HttpOnly cookie + Redis session

| Layer | Role |
| --- | --- |
| **Cookie** | `session_id` — HttpOnly, SameSite=Lax, Secure in production |
| **Cache** | `infrastructure/cache/redis.py` — `session:{id}` → `{user_id, created_at}` with TTL |
| **JWT** | Optional for OpenAPI / tests / API clients (`Authorization: Bearer`) |

**Flow:** login/register → Redis session → Set-Cookie → `/me` reads cookie → logout deletes session + clears cookie.

Browser UI uses `credentials: include` — **no token in localStorage**.

**Code:**

| Concern | Path |
| --- | --- |
| Session cookie helpers | `app/core/cookies.py` |
| Redis session store | `app/infrastructure/cache/redis.py` |
| JWT creation / verify | `app/core/security.py` |
| Current user dependency | `app/core/dependencies.py` |
| Auth routes | `app/api/v1/auth/router.py` |

---

## Rate limiting

| Scope | Where | Limit |
| --- | --- | --- |
| **Per IP** | `RateLimitMiddleware` (all routes except health/docs) | `RATE_LIMIT_IP_PER_MINUTE` |
| **Per user** | `enforce_rate_limit` on chat | `RATE_LIMIT_PER_MINUTE` |

Redis down → fail open (availability).

| Module | Path |
| --- | --- |
| IP middleware | `app/core/middleware.py` |
| User chat limit | `app/core/logging.py` (`enforce_rate_limit`) |
| Redis client | `app/infrastructure/cache/redis.py` |

---

## Errors

All API errors use one JSON envelope:

```json
{ "error": { "code": "...", "message": "...", "fields": [] } }
```

- Empty or undefined messages are never returned
- Validation → field-level `fields[]`
- No stack traces in responses

| Module | Path |
| --- | --- |
| Domain exceptions | `app/core/exceptions/domain.py` |
| Handlers | `app/core/exceptions/handlers.py` |
| Registration | `app/core/exceptions/register.py` |

---

## Performance

| Technique | Where |
| --- | --- |
| **Composite indexes** | `messages(conversation_id, created_at)`, `conversations(user_id, updated_at)` |
| **N+1 prevention** | `selectinload(Conversation.messages)` on detail fetch |
| **List limits** | conversations (100), documents (200) |
| **No eager load on lists** | sidebar list = metadata only |

Indexes applied on `init_db()` and Alembic `002_create_conversations` / `003_create_documents`.

---

## Data isolation

- All conversation and document queries are scoped by `user_id`
- Cross-user access returns `404` (not `403`) to avoid leaking resource existence
- Passwords stored as bcrypt hashes only — never returned in API responses

---

## Related docs

| Document | Purpose |
| --- | --- |
| [../backend/README.md](../backend/README.md) | Architecture, env vars, migrations, pytest, Ruff |
| [../frontend/README.md](../frontend/README.md) | TypeScript, ESLint, Prettier, Jest |
| [TESTING.md](TESTING.md) | Auth and rate-limit test coverage |
| [PRESENTATION.md](PRESENTATION.md) | Demo walkthrough |
