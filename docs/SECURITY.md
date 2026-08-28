# Security & performance

Production-oriented auth, rate limiting, errors, and database tuning.

## Auth: HttpOnly cookie + Redis session

| Layer | Role |
| --- | --- |
| **Cookie** | `session_id` — HttpOnly, SameSite=Lax, Secure in production |
| **Redis** | `session:{id}` → `{user_id, created_at}` with TTL |
| **JWT (body)** | Optional for OpenAPI / tests / API clients (`Authorization: Bearer`) |

**Flow:** login/register → Redis session → Set-Cookie → `/me` reads cookie → logout deletes Redis + clears cookie.

Browser UI uses `credentials: include` — **no token in localStorage**.

## Rate limiting

| Scope | Where | Limit |
| --- | --- | --- |
| **Per IP** | `RateLimitMiddleware` on all routes (except health/docs) | `RATE_LIMIT_IP_PER_MINUTE` |
| **Per user** | `enforce_rate_limit` on chat | `RATE_LIMIT_PER_MINUTE` |

Redis down → fail open (availability).

## Errors

All API errors use one JSON envelope:

```json
{ "error": { "code": "...", "message": "...", "fields": [] } }
```

- Empty or undefined messages are never returned
- Validation → field-level `fields[]`
- No stack traces in responses

## Performance

| Technique | Where |
| --- | --- |
| **Composite indexes** | `messages(conversation_id, created_at)`, `conversations(user_id, updated_at)` |
| **N+1 prevention** | `selectinload(Conversation.messages)` on detail fetch |
| **List limits** | conversations (100), documents (200) |
| **No eager load on lists** | sidebar list = metadata only |

Indexes applied on `init_db()` and Alembic `002_perf_indexes`.
