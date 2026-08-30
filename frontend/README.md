# Next.js Frontend

Chat UI for the FastAPI backend — auth, conversation sidebar, streaming chat, and knowledge upload.

Runs locally with **npm** (no Docker required for the frontend).

**Core stack:** TypeScript + ESLint + Prettier.

---

## Quick start

```powershell
# Terminal 1 — backend
cd ..\backend
Copy-Item .env.example .env
docker compose up --build

# New terminal — after Postgres is up
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

The proxy at `src/app/api/v1/[...path]/route.ts` forwards cookies to FastAPI. If the backend is down, API calls return **503**.

---

## Database migrations & seeds

Run from `../backend/`. Full reference: [../backend/README.md](../backend/README.md#database-migrations--seeds).

### Migrations

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Apply all | `docker compose run --rm api alembic upgrade head` | `alembic upgrade head` |
| Revert last | `docker compose run --rm api alembic downgrade -1` | `alembic downgrade -1` |
| Current revision | `docker compose run --rm api alembic current` | `alembic current` |
| New migration | `docker compose run --rm api alembic revision --autogenerate -m "msg"` | `alembic revision --autogenerate -m "msg"` |

### Seeds

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Seed demo data | `docker compose run --rm api python alembic/seeds/run.py` | `python alembic/seeds/run.py` |
| Seed + embed | `docker compose run --rm api python alembic/seeds/run.py --embed` | `python alembic/seeds/run.py --embed` |

---

## Routes

| Path | Use |
| --- | --- |
| `/login` | Sign in |
| `/register` | Create account |
| `/chat` | Chat UI + sidebar |
| `/knowledge` | Upload and list RAG documents |

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
    │   ├── (auth)/login, register
    │   ├── (dashboard)/chat, knowledge
    │   └── api/v1/[...path]/route.ts   # Proxy to FastAPI
    ├── features/                        # auth, chat, conversations, knowledge, health
    ├── components/ui/                   # Shared UI primitives
    └── lib/                             # api client, SSE reader
```

| Feature | Folder | Backend |
| --- | --- | --- |
| Auth | `features/auth/` | `/auth/*` |
| Chat | `features/chat/` | `POST /chat/stream` |
| Conversations | `features/conversations/` | `GET /conversations` |
| Knowledge | `features/knowledge/` | `GET/POST /documents` |
| Health | `features/health/` | `GET /health` |

---

## Chat streaming (SSE)

`POST /chat/stream` events:

| Event | UI behavior |
| --- | --- |
| `meta` | Set `conversation_id` in sidebar |
| `token` | Append assistant text |
| `done` | Finalize message, refresh list |
| `error` | Show `LLM_ERROR` (not mixed into tokens) |

Handled in `features/chat/hooks.ts` via `lib/sse/reader.ts`.

---

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI URL for the proxy |

---

## Tooling

### TypeScript

| Library | Role |
| --- | --- |
| **TypeScript 5** | Static typing (`strict: true`) |

Config: `tsconfig.json` · Path alias: `@/*` → `src/*`

| Action | Command |
| --- | --- |
| Type check | `npm run typecheck` |
| Build (includes type check) | `npm run build` |

### Lint — ESLint

| Library | Role |
| --- | --- |
| **ESLint** | Linter |
| **eslint-config-next** | Next.js + React rules (`core-web-vitals`, `typescript`) |
| **eslint-config-prettier** | Disables ESLint rules that conflict with Prettier |

Config: `.eslintrc.json`

| Action | Command |
| --- | --- |
| Lint | `npm run lint` |
| Lint + fix | `npm run lint:fix` |

### Format — Prettier

| Library | Role |
| --- | --- |
| **Prettier** | Code formatter |

Config: `.prettierrc` (`printWidth: 88`, double quotes)

| Action | Command |
| --- | --- |
| Format all | `npm run format` |
| Check formatting | `npm run format:check` |

### Test — Jest

| Library | Role |
| --- | --- |
| **Jest** | Unit / component / integration test runner |
| **React Testing Library** | Component and hook tests |
| **@testing-library/user-event** | User interaction simulation |

Config: `jest.config.mjs`

| Action | Command |
| --- | --- |
| All tests | `npm test` |
| Unit only | `npm run test:unit` |
| Components | `npm run test:components` |
| Integration | `npm run test:integration` |

### E2E — Playwright

| Library | Role |
| --- | --- |
| **Playwright** | Browser end-to-end tests |

Config: `playwright.config.ts`

| Action | Command |
| --- | --- |
| Run e2e | `npm run test:e2e` |
| Interactive UI | `npm run test:e2e:ui` |

Requires backend running at `http://localhost:8000`.

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
| [../backend/README.md](../backend/README.md) | API, migrations, seeds, pytest, Ruff |
| [../docs/TESTING.md](../docs/TESTING.md) | Test strategy |
| [../docs/PRESENTATION.md](../docs/PRESENTATION.md) | Demo script |
