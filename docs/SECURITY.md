# Security

Q2 minimal stack — JWT authentication, bcrypt passwords, structured API errors.

No Redis sessions, no cookie-based auth, no rate-limit middleware.

---

## Auth: JWT (Bearer token)

| Layer | Role |
| --- | --- |
| **Register / login** | Returns `access_token` (JWT) |
| **Protected routes** | `Authorization: Bearer <token>` |
| **Frontend** | Token in `sessionStorage` via `lib/auth/token.ts` |
| **Logout** | Client clears token (stateless JWT) |

**Code:**

| Concern | Path |
| --- | --- |
| JWT create / verify | `app/core/security.py` |
| Current user dependency | `app/core/dependencies.py` |
| Auth routes | `app/api/v1/auth/router.py` |
| Frontend token helper | `frontend/src/lib/auth/token.ts` |
| API client headers | `frontend/src/lib/api/client.ts` |

### Auth flow

```
POST /auth/login → JWT returned → sessionStorage
GET  /auth/me    → Authorization: Bearer <token>
POST /chat/stream → same Bearer header
```

---

## Errors

All API errors use one JSON envelope:

```json
{ "error": { "code": "...", "message": "...", "fields": [] } }
```

| Code | HTTP | When |
| --- | --- | --- |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `CONVERSATION_NOT_FOUND` | 404 | Wrong or missing thread |
| `LLM_ERROR` | 502 | Upstream model failure |
| `VALIDATION_ERROR` | 422 | Blank message, bad input |

SSE streams emit `error` events (not HTTP errors) for LLM failures mid-stream.

---

## Database

- Passwords hashed with bcrypt (`app/core/security.py`)
- Foreign keys with `ON DELETE CASCADE` for conversations/messages
- Indexes on hot query paths (`messages.conversation_id`, `conversations.user_id`)
- Users can only access their own conversations (enforced in `ChatService`)

---

## CORS

Configured via `CORS_ORIGINS` in `.env`. Default allows `http://localhost:3000`.

---

## Production checklist

- Set `JWT_SECRET_KEY` (min 32 chars, unique per environment)
- Set `APP_ENV=production` and use HTTPS
- Restrict `CORS_ORIGINS` to your frontend domain
- Never commit `.env` with real API keys
- Rotate `GEMINI_API_KEY` / `OPENAI_API_KEY` if exposed

---

## Related docs

[../README.md](../README.md) · [../backend/README.md](../backend/README.md) · [TESTING.md](TESTING.md)
