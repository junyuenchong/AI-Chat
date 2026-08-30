# FastAPI Backend

REST API for AI chat, conversation history, knowledge documents, and authentication.

Runs in **Docker** (recommended) or **locally** with Python + Uvicorn. Postgres and Redis via Docker Compose.

---

## Quick start

### Docker (recommended)

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build

# New terminal — after Postgres is up
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

Frontend: `cd ../frontend && npm install && npm run dev`

### Local Python

Requires **Python 3.12+**. Postgres and Redis still run in Docker.

```powershell
cd backend
Copy-Item .env.example .env
docker compose up postgres redis -d

# Uncomment localhost lines in .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python alembic/seeds/run.py

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
arq app.infrastructure.messaging.worker.WorkerSettings   # separate terminal
```

### URLs

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| Adminer | http://localhost:8080 |

**Demo login:** `demo@example.com` / `demo123`

Leave `GEMINI_API_KEY` empty for **demo mode** (real HTTP, DB, SSE; mock LLM text).

### Common commands

```powershell
docker compose logs -f api worker
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
docker compose run --rm api pytest
.\scripts\ruff.ps1
docker compose down -v          # reset DB volumes
```

---

## Database migrations & seeds

| | Path |
| --- | --- |
| Schema | `app/infrastructure/database/models.py` |
| Migrations | `alembic/versions/` |
| Seeds | `alembic/seeds/` |

| Revision | File | Creates |
| --- | --- | --- |
| `001_create_users` | `001_create_users.py` | Extensions + `users` |
| `002_create_conversations` | `002_create_conversations.py` | `conversations`, `messages` |
| `003_create_documents` | `003_create_documents.py` | `documents`, `document_chunks` |

### Migrations

Run from `backend/`.

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Apply all | `docker compose run --rm api alembic upgrade head` | `alembic upgrade head` |
| Revert last | `docker compose run --rm api alembic downgrade -1` | `alembic downgrade -1` |
| Current revision | `docker compose run --rm api alembic current` | `alembic current` |
| New migration | `docker compose run --rm api alembic revision --autogenerate -m "msg"` | `alembic revision --autogenerate -m "msg"` |

After editing `models.py`: autogenerate → review `alembic/versions/` → `upgrade head`.

### Seeds

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Seed demo data | `docker compose run --rm api python alembic/seeds/run.py` | `python alembic/seeds/run.py` |
| Seed + embed | `docker compose run --rm api python alembic/seeds/run.py --embed` | `python alembic/seeds/run.py --embed` |

| Seed file | Data |
| --- | --- |
| `alembic/seeds/users.py` | Demo user + starter conversation |
| `alembic/seeds/documents.py` | `hr-policy.md`, `onboarding.md` |
| `alembic/seeds/run.py` | Orchestrator |

Idempotent — safe to re-run.

**Reset database:**

```powershell
docker compose down -v
docker compose up -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

---

## Stack

| Component | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Database | PostgreSQL + pgvector |
| AI | LangChain (LLM + embeddings) |
| Cache | Redis (sessions, rate limits) |
| Jobs | Redis + ARQ (embeddings, summaries) |
| Auth | JWT + HttpOnly session cookie |

---

## Project structure

```
backend/
├── alembic/
│   ├── versions/          # schema migrations
│   ├── seeds/             # reference data
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── main.py
│   ├── core/              # config, security, middleware, dependencies
│   ├── api/v1/            # routers + dto/request.py + dto/response.py
│   ├── application/       # services + mapper.py per feature
│   ├── domain/            # entities.py + ports.py
│   ├── shared/            # constants, types, retry helpers
│   └── infrastructure/
│       ├── ai/langchain/  # llm, embeddings, prompts, retrieval, tools, agent
│       ├── database/      # models, repositories, session
│       ├── vector/        # pgvector queries
│       ├── cache/         # redis
│       └── messaging/     # ARQ queue, worker, tasks
```

`shared/retry.py` — exponential backoff for transient LLM/embedding API errors.

### Request flow

```
HTTP Request
  → api/dto/request.py
  → application/mapper.py
  → application/service.py
  → domain/entities + ports
  → infrastructure/
  → application/mapper.py
  → api/dto/response.py
  → HTTP Response
```

**Rules:** Routers stay thin. Application never returns API DTOs. LangChain stays in `infrastructure/ai/`.

---

## LLM, RAG, and resilience

| Component | Role |
| --- | --- |
| `application/chat/service.py` | Use case — persistence, SSE, rate limits |
| `domain/chat/ports.py` | `ChatEngine` port |
| `infrastructure/ai/langchain/agent.py` | RAG routing + stream/complete |
| `infrastructure/ai/langchain/llm.py` | LLM providers + model failover chain |
| `infrastructure/ai/langchain/embeddings.py` | Embeddings with retry |
| `infrastructure/ai/langchain/retrieval.py` | pgvector + keyword search |
| `shared/retry.py` | Exponential backoff for transient API errors |

### RAG modes

| `RAG_STRICT_MODE` | No KB hit |
| --- | --- |
| `true` | Refuse — no LLM call |
| `false` | Fall back to LLM general knowledge |

Retrieval order: **vector search → keyword → fallback chunks** (hybrid only).

### LLM resilience

Per model, on transient failure (429, 503, timeout):

1. **Retry** with exponential backoff (`LLM_RETRY_*` settings)
2. **Failover** to `GEMINI_FALLBACK_MODEL`, then OpenAI (if key configured)
3. Return `LLM_ERROR` to the client if all models fail

Streaming retries only **before** the first token is sent (no partial-stream retry).

Embeddings (`embed_query`, `embed_text_chunks`) use the same retry settings.

ARQ worker: `max_tries = 3` for `process_document` and `summarize_conversation`.

---

## API routes

Base path: `/api/v1`. Swagger: http://localhost:8000/docs

### Health

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/health` | Status — LLM, Postgres, Redis |

### Auth

| Method | Path | Use |
| --- | --- | --- |
| `POST` | `/auth/register` | Create account + session |
| `POST` | `/auth/login` | Log in |
| `POST` | `/auth/logout` | End session |
| `GET` | `/auth/me` | Current user (cookie or Bearer JWT) |

### Conversations

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/conversations` | List threads |
| `GET` | `/conversations/{id}` | Load thread + messages |
| `DELETE` | `/conversations/{id}` | Delete thread |

### Chat

| Method | Path | Use |
| --- | --- | --- |
| `POST` | `/chat/stream` | Stream reply (SSE) |
| `POST` | `/chat/complete` | Full reply (JSON) |

### Documents

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/documents` | List documents |
| `POST` | `/documents` | Upload + enqueue embedding |
| `DELETE` | `/documents/{id}` | Delete document |

---

## Key flows

### Chat stream

```
POST /chat/stream → rate limit → save message → RAG (optional)
  → stream LLM (meta → token → done) → save reply → maybe summarize
```

| SSE event | Payload |
| --- | --- |
| `meta` | `conversation_id`, `llm`, `route` |
| `token` | `{ "content": "..." }` |
| `done` | `conversation_id`, `content`, `route`, `rag` |
| `error` | `{ "code": "LLM_ERROR", "message": "..." }` |

Transient LLM failures are retried (exponential backoff + model failover) before an `error` event is sent.

### Document upload

```
POST /documents → save row → chunk text → ARQ embed job → pgvector
```

Without an API key, keyword search still works; embeddings stay empty.

### Background jobs

| Job | Trigger | Action | Retries |
| --- | --- | --- | --- |
| `process_document` | After upload | Chunk + embed → pgvector | Up to 3 (ARQ) |
| `summarize_conversation` | Every 4 messages | LLM summary → `Conversation.summary` | Up to 3 (ARQ) |

Worker: `arq app.infrastructure.messaging.worker.WorkerSettings` (Docker `worker` service).

---

## Docker services

| Service | Port | Role |
| --- | --- | --- |
| `api` | 8000 | FastAPI |
| `worker` | — | ARQ jobs |
| `postgres` | 5432 | PostgreSQL + pgvector |
| `redis` | 6379 | Cache + queue |
| `adminer` | 8080 | DB admin UI |

---

## Environment variables

Copy `.env.example` → `.env`. All keys in `app/core/config.py`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `@postgres:5432` | Use `@localhost` for local Python |
| `REDIS_URL` | `redis://redis:6379/0` | Use `localhost` for local Python |
| `GEMINI_API_KEY` | _(empty)_ | Empty = demo mode |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Primary chat model |
| `GEMINI_FALLBACK_MODEL` | _(empty)_ | Secondary Gemini model on primary failure |
| `LLM_RETRY_MAX_ATTEMPTS` | `3` | Retries per model on transient errors |
| `LLM_RETRY_BASE_DELAY_SECONDS` | `0.5` | Initial backoff between retries |
| `LLM_RETRY_MAX_DELAY_SECONDS` | `8.0` | Max backoff cap |
| `RAG_STRICT_MODE` | `false` | Strict vs hybrid RAG |
| `RAG_MAX_DISTANCE` | `0.45` | pgvector relevance threshold |
| `JWT_SECRET_KEY` | _(dev)_ | Token signing |
| `RATE_LIMIT_PER_MINUTE` | `30` | Per-user chat limit |

Full list: `.env.example`

---

## Tooling

### Test — pytest

| Library | Role |
| --- | --- |
| **pytest** | Test runner |
| **pytest-asyncio** | Async test support (`asyncio_mode = auto`) |
| **httpx** | HTTP client for integration/e2e tests |

Config: `pytest.ini` · Markers: `unit`, `integration`, `e2e`

| Action | Docker | Local (venv) |
| --- | --- | --- |
| All tests | `docker compose run --rm api pytest` | `pytest` |
| Unit only | `docker compose run --rm api pytest -m unit` | `pytest -m unit` |
| Integration | `docker compose run --rm api pytest -m integration` | `pytest -m integration` |
| E2E | `docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e` | `pytest -m e2e` |

| Layer | Folder | Covers |
| --- | --- | --- |
| Unit | `tests/unit/` | DTOs, mappers, RAG, retry, LLM failover, JWT, rate limits |
| Integration | `tests/integration/` | Auth, chat, SSE, documents |
| E2E | `tests/e2e/` | Register → chat smoke |

### Format & lint — Ruff

| Library | Role |
| --- | --- |
| **Ruff** | Formatter + linter (replaces Black, isort, flake8) |

Config: `pyproject.toml` (`line-length = 88`, rules: E, F, I, UP, B)

| Action | Command |
| --- | --- |
| Format + lint (recommended) | `.\scripts\ruff.ps1` |
| Format only | `ruff format .` |
| Lint + auto-fix | `ruff check . --fix` |
| Lint (check only) | `ruff check .` |

Install: `winget install astral-sh.ruff` or `pip install -r requirements-dev.txt`

### Type checking

Python uses **type hints** throughout. IDE: **Pylance**. Ruff `UP` rules catch common typing issues.

---

## Security

[../docs/SECURITY.md](../docs/SECURITY.md) — sessions, cookies, rate limits, auth.

---

## Related docs

| Document | Contents |
| --- | --- |
| [../README.md](../README.md) | Project overview |
| [../frontend/README.md](../frontend/README.md) | TypeScript, ESLint, Prettier, Jest |
| [../docs/TESTING.md](../docs/TESTING.md) | Test strategy |
| [../docs/PRESENTATION.md](../docs/PRESENTATION.md) | Demo script |
