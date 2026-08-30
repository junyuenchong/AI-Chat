# AI Chat

Full-stack **streaming LLM chat** (Question 2 assignment) with optional **traditional RAG** knowledge grounding.

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 15, TypeScript, ESLint, Prettier |
| Backend | FastAPI, Python 3.12, Ruff |
| AI | LangChain (Gemini or OpenAI) |
| Data | PostgreSQL + pgvector, Redis |

**Highlights:** SSE token streaming · Postgres session memory · RAG document upload · retry + model failover · Docker Compose · unit / integration / e2e tests

---

## Quick start

### Backend

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build

# New terminal — after Postgres is up
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

### Frontend

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

### URLs

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| Adminer | http://localhost:8080 |

**Demo login** (after seeding): `demo@example.com` / `demo123`

---

## Database migrations & seeds

Run from `backend/`. Full reference: [backend/README.md](backend/README.md#database-migrations--seeds).

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

**Reset database:**

```powershell
cd backend
docker compose down -v
docker compose up -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

---

## API overview

Base path: `/api/v1`. Details: [backend/README.md](backend/README.md#api-routes).

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/health` | Service status |
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Log in |
| `POST` | `/auth/logout` | Log out |
| `GET` | `/auth/me` | Current user |
| `GET` | `/conversations` | List threads |
| `GET` | `/conversations/{id}` | Load thread |
| `DELETE` | `/conversations/{id}` | Delete thread |
| `POST` | `/chat/stream` | Stream reply (SSE) |
| `POST` | `/chat/complete` | Full reply (JSON) |
| `GET` | `/documents` | List documents |
| `POST` | `/documents` | Upload document |
| `DELETE` | `/documents/{id}` | Delete document |

---

## Configuration

| Setting | Behavior |
| --- | --- |
| `GEMINI_API_KEY` or `OPENAI_API_KEY` set | Real LLM via LangChain |
| Keys empty | Demo mode — mock LLM text, real HTTP/DB/SSE |
| `RAG_STRICT_MODE=true` | Refuse when no knowledge-base hit |
| `RAG_STRICT_MODE=false` | Fall back to LLM general knowledge |
| `GEMINI_FALLBACK_MODEL` | Secondary Gemini model when primary fails |
| `LLM_RETRY_MAX_ATTEMPTS` | Retries on transient errors (429, 503, timeouts) before failover |
| `LLM_RETRY_BASE_DELAY_SECONDS` | Initial backoff delay between retries |
| `LLM_RETRY_MAX_DELAY_SECONDS` | Cap on exponential backoff delay |

### Resilience (LLM + embeddings)

```
Transient error (429/503/timeout)
  → retry with exponential backoff (up to LLM_RETRY_MAX_ATTEMPTS)
  → failover to GEMINI_FALLBACK_MODEL or OpenAI
  → user sees LLM_ERROR if all models fail
```

RAG retrieval uses a separate fallback chain: **vector search → keyword → first chunks** (hybrid mode only).

Background embed jobs retry up to **3 times** via ARQ (`max_tries` on the worker).

---

## Tooling

### Backend (Python)

| Tool | Library | Config | Command |
| --- | --- | --- | --- |
| **Test** | pytest, pytest-asyncio, httpx | `pytest.ini` | `docker compose run --rm api pytest` |
| **Format** | Ruff | `pyproject.toml` | `ruff format .` |
| **Lint** | Ruff | `pyproject.toml` | `ruff check .` |
| **Format + lint** | Ruff | `pyproject.toml` | `.\scripts\ruff.ps1` |

```powershell
cd backend
docker compose run --rm api pytest -m unit
docker compose run --rm api pytest -m integration
.\scripts\ruff.ps1
```

### Frontend (TypeScript)

| Tool | Library | Config | Command |
| --- | --- | --- | --- |
| **TypeScript** | TypeScript 5 (strict) | `tsconfig.json` | `npm run typecheck` |
| **Lint** | ESLint, eslint-config-next | `.eslintrc.json` | `npm run lint` |
| **Format** | Prettier, eslint-config-prettier | `.prettierrc` | `npm run format` |
| **Test** | Jest, React Testing Library | `jest.config.mjs` | `npm test` |
| **E2E** | Playwright | `playwright.config.ts` | `npm run test:e2e` |

```powershell
cd frontend
npm run typecheck
npm run lint
npm run format:check
npm test
npm run test:e2e
```

Details: [backend/README.md](backend/README.md#tooling) · [frontend/README.md](frontend/README.md#tooling) · [docs/TESTING.md](docs/TESTING.md)

---

## Architecture

```
Browser (Next.js)
  → api/v1/ (routers + dto)
  → application/ (services + mappers)
  → domain/ (entities + ports)
  → infrastructure/ (LangChain, Postgres, Redis, pgvector)
  → shared/ (retry helpers, constants)
```

Details: [backend/README.md](backend/README.md#project-structure)

---

## Repository

```
FastApi/
├── backend/     API, AI, database, Docker Compose
├── frontend/    Next.js chat UI
└── docs/        Testing, security, presentation
```

| Document | Contents |
| --- | --- |
| [backend/README.md](backend/README.md) | Architecture, API, retry/failover, migrations, seeds, pytest, Ruff |
| [frontend/README.md](frontend/README.md) | UI, TypeScript, ESLint, Prettier, Jest, Playwright |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy |
| [docs/SECURITY.md](docs/SECURITY.md) | Auth and rate limits |
| [docs/PRESENTATION.md](docs/PRESENTATION.md) | Demo script |
