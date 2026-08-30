# Next.js Frontend (Question 2)

Chat UI for the FastAPI backend — JWT auth, conversation sidebar, and SSE streaming chat.

Runs locally with **npm** (no Docker required for the frontend).

**Core stack:** Next.js 15 · React 19 · TypeScript · Tailwind CSS 4 · ESLint · Prettier

**Not in scope:** knowledge upload · RAG UI · cookie-based sessions · Redis

---

## Quick start

```powershell
# Terminal 1 — backend
cd ..\backend
Copy-Item .env.example .env
docker compose down -v --remove-orphans   # optional — fresh DB
docker compose up --build

# New terminal — after Postgres is healthy
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py

# Terminal 2 — frontend
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000** → `/chat`.

**Demo login:** `demo@example.com` / `demo123`

**New email?** Use **Register** — login does not create accounts.

JWT is stored in `sessionStorage` and sent as `Authorization: Bearer` on API calls.

---

## Architecture

```
Browser
   ↓
Next.js (features/chat)
   ↓  Authorization: Bearer <JWT>
/api/v1/[...path]/route.ts   ← same-origin proxy (forwards auth + SSE)
   ↓
FastAPI POST /chat/stream
   ↓
SSE: meta → token → token → … → done
```

In the browser, `lib/api/client.ts` calls `/api/v1/*` (same origin). The Next.js route handler proxies to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Postgres history is managed by the backend. The frontend only sends messages and renders streamed tokens.

---

## Routes

| Path | Use |
| --- | --- |
| `/login` | Sign in |
| `/register` | Create account |
| `/chat` | Chat UI + conversation sidebar |

Unauthenticated users are redirected to `/login`. Signed-in users on auth pages are redirected to `/chat`.

---

## Project structure

```
frontend/
├── .eslintrc.json
├── .prettierrc
├── tsconfig.json
├── jest.config.mjs
├── playwright.config.ts
└── src/
    ├── app/
    │   ├── (auth)/login, register     # AuthLayout — redirect if signed in
    │   ├── (dashboard)/chat           # DashboardLayout — sidebar + chat
    │   ├── api/v1/[...path]/route.ts  # Proxy to FastAPI (auth + SSE)
    │   └── providers.tsx              # AuthProvider wrapper
    ├── features/                      # auth, chat, conversations, health
    ├── components/ui/                 # Shared UI primitives
    └── lib/                           # api client, auth token, SSE reader
```

| Feature | Folder | Backend |
| --- | --- | --- |
| Auth | `features/auth/` | `POST /auth/login`, `POST /auth/register`, `GET /auth/me` |
| Chat | `features/chat/` | `POST /chat/stream`, `POST /chat/complete` |
| Conversations | `features/conversations/` | `GET /conversations`, `GET /conversations/{id}` |
| Health | `features/health/` | `GET /health` |

---

## Chat streaming (SSE)

`POST /chat/stream` events:

| Event | UI behavior |
| --- | --- |
| `meta` | Set `conversation_id`, show LLM provider |
| `token` | Append assistant text live |
| `done` | Finalize message, refresh sidebar |
| `error` | Show error in assistant bubble |

Handled in `features/chat/hooks.ts` via `lib/sse/reader.ts`.

The backend retries transient LLM failures (429, 503, timeouts) with exponential backoff and model failover before emitting `error`.

---

## Auth

| Concern | Path |
| --- | --- |
| Token storage | `lib/auth/token.ts` (`sessionStorage`) |
| API client | `lib/api/client.ts` (`Authorization: Bearer`) |
| Auth context | `features/auth/AuthProvider.tsx` |
| Login / register forms | `features/auth/components/AuthForm.tsx` |

| Behavior | Detail |
| --- | --- |
| Page load | `fetchCurrentUser()` skips `/auth/me` when no token |
| 401 on `/auth/me` | Token cleared — treated as logged out |
| Logout | `clearAccessToken()` only (stateless JWT) |

---

## Code comments

Source files use the same style as the backend:

- **Module docstring** — request path (which component calls this file)
- **Boxed block comment** per function — Path, Endpoint, Use
- **Inline steps** — `// Step 1 — ...` inside handlers

Key files: `lib/api/client.ts`, `features/chat/hooks.ts`, `features/auth/AuthProvider.tsx`, `app/api/v1/[...path]/route.ts`

---

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI URL for the Next.js proxy |

Copy `.env.local.example` → `.env.local`.

---

## Database migrations & seeds

Run from `../backend/`. Full reference: [../backend/README.md](../backend/README.md#database-migrations--seeds).

| Action | Docker |
| --- | --- |
| Migrate | `docker compose run --rm api alembic upgrade head` |
| Seed | `docker compose run --rm api python alembic/seeds/run.py` |

---

## Tooling

### TypeScript

| Action | Command |
| --- | --- |
| Type check | `npm run typecheck` |
| Build | `npm run build` |

Path alias: `@/*` → `src/*`

### Lint & format

| Action | Command |
| --- | --- |
| Lint | `npm run lint` |
| Lint + fix | `npm run lint:fix` |
| Format | `npm run format` |
| Check formatting | `npm run format:check` |

### Test — Jest (41 tests)

| Action | Command |
| --- | --- |
| All tests | `npm test` |
| Unit only | `npm run test:unit` |
| Components | `npm run test:components` |
| Integration | `npm run test:integration` |

| Test file | Focus |
| --- | --- |
| `tests/unit/lib/api/client.test.ts` | API client, auth headers, errors |
| `tests/unit/lib/sse/reader.test.ts` | SSE parsing |
| `tests/unit/features/auth/api.test.ts` | Register, login, `/auth/me` |
| `tests/unit/features/chat/api.test.ts` | Stream chat API |
| `tests/unit/features/chat/hooks.test.tsx` | `useChat` hook |
| `tests/unit/features/health/hooks.test.tsx` | Health polling |
| `tests/integration/chat-stream.integration.test.tsx` | SSE integration |
| `tests/components/AuthForm.test.tsx` | Auth form UI |
| `tests/components/chat-ui.test.tsx` | Chat components |

### E2E — Playwright

| Action | Command |
| --- | --- |
| Run e2e | `npm run test:e2e` |
| Interactive UI | `npm run test:e2e:ui` |

Requires backend running at `http://localhost:8000`.

| Spec | Focus |
| --- | --- |
| `tests/e2e/auth.spec.ts` | Login / register |
| `tests/e2e/chat.spec.ts` | Chat UI |

### Quality check (all)

```powershell
cd frontend
npm run typecheck
npm run lint
npm run format:check
npm test
```

---

## Related docs

| Document | Contents |
| --- | --- |
| [../README.md](../README.md) | Project overview |
| [../backend/README.md](../backend/README.md) | API, migrations, pytest, Ruff |
| [../docs/TESTING.md](../docs/TESTING.md) | Test strategy |
| [../docs/PRESENTATION.md](../docs/PRESENTATION.md) | Demo script |
| [../docs/SECURITY.md](../docs/SECURITY.md) | JWT auth |
