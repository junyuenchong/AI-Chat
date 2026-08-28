# FastAPI Backend

REST API for AI chat, conversation history, knowledge documents, and authentication.

Runs in **Docker** (API + worker + Postgres + Redis), or **locally** with Python + Uvicorn (Postgres/Redis via Docker). The Next.js UI lives in `../frontend`.

---

## Quick start

### Option A — Docker (full stack)

```powershell
# 1. Backend
cd backend
Copy-Item .env.example .env
docker compose up --build

# 2. Database migrations (new terminal, after Postgres is up)
cd backend
docker compose run --rm api alembic upgrade head

# 3. Frontend (new terminal)
cd ..\frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev

# 4. Format + lint (optional — no Python venv required)
cd ..\backend
.\scripts\ruff.ps1
```

> On first `docker compose up`, `init_db()` also creates tables automatically. Run `alembic upgrade head` to apply versioned migrations (recommended after pulling schema changes).

### Option B — Local Python (API on host, no Docker for api/worker)

Requires **Python 3.12+**. Postgres and Redis still run in Docker (pgvector image).

```powershell
# 1. Infra only (Postgres + Redis)
cd backend
Copy-Item .env.example .env
docker compose up postgres redis -d

# 2. For local Python only — uncomment localhost lines in `.env` (see .env.example)
#    DATABASE_URL=...@localhost:5432/...
#    REDIS_URL=redis://localhost:6379/0

# 3. Python venv + dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Database migrations
alembic upgrade head

# 5. Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Worker (new terminal — optional, for document embedding + summaries)
cd backend
.\.venv\Scripts\Activate.ps1
arq app.infrastructure.queue.worker.WorkerSettings

# 7. Frontend (new terminal)
cd ..\frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

**Local tests** (Postgres + Redis must be running):

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

### URLs

| Service            | URL                                 |
| ------------------ | ----------------------------------- |
| Chat UI            | http://localhost:3000               |
| API docs (Swagger) | http://localhost:8000/docs          |
| Health             | http://localhost:8000/api/v1/health |
| Adminer (DB UI)    | http://localhost:8080               |

Register or log in from the UI. Leave `GEMINI_API_KEY` empty for **demo mode** (real HTTP, DB, SSE; mock LLM text).

### Common commands (Docker)

```powershell
# Database migrations — apply
docker compose run --rm api alembic upgrade head

# Database migrations — revert last
docker compose run --rm api alembic downgrade -1

# Inspect
docker compose run --rm api alembic current
docker compose run --rm api alembic history

# Logs
docker compose logs -f api worker

# Run tests in container
docker compose run --rm api pytest

# Stop and remove volumes (reset DB)
docker compose down -v
```

### Database migrations (reference)

All commands below use **Alembic** (SQLAlchemy 2.0). Replace the local column with the Docker column when using containers.

#### Apply migrations (upgrade)

| Action | Docker | Local (venv active) |
| --- | --- | --- |
| Apply all pending | `docker compose run --rm api alembic upgrade head` | `alembic upgrade head` |
| Apply next one only | `docker compose run --rm api alembic upgrade +1` | `alembic upgrade +1` |
| Upgrade to revision | `docker compose run --rm api alembic upgrade 002_perf_indexes` | `alembic upgrade 002_perf_indexes` |

#### Revert migrations (downgrade)

| Action | Docker | Local (venv active) |
| --- | --- | --- |
| Revert last migration | `docker compose run --rm api alembic downgrade -1` | `alembic downgrade -1` |
| Revert last N migrations | `docker compose run --rm api alembic downgrade -2` | `alembic downgrade -2` |
| Downgrade to revision | `docker compose run --rm api alembic downgrade 001_initial` | `alembic downgrade 001_initial` |
| Revert all (empty schema) | `docker compose run --rm api alembic downgrade base` | `alembic downgrade base` |

#### Create & inspect

| Action | Docker | Local (venv active) |
| --- | --- | --- |
| New migration (autogenerate) | `docker compose run --rm api alembic revision --autogenerate -m "msg"` | `alembic revision --autogenerate -m "msg"` |
| New empty migration | `docker compose run --rm api alembic revision -m "msg"` | `alembic revision -m "msg"` |
| Current revision | `docker compose run --rm api alembic current` | `alembic current` |
| History | `docker compose run --rm api alembic history` | `alembic history` |
| Verbose history | `docker compose run --rm api alembic history --verbose` | `alembic history --verbose` |
| Mark DB at revision (no SQL) | `docker compose run --rm api alembic stamp head` | `alembic stamp head` |

Migration files: `alembic/versions/` (`001_initial`, `002_perf_indexes`). Full guide: [Database migrations (SQLAlchemy 2.0 + Alembic)](#database-migrations-sqlalchemy-20--alembic).

---

## Stack

| Component     | Technology                                      |
| ------------- | ----------------------------------------------- |
| API           | FastAPI, Uvicorn                                |
| ORM           | **SQLAlchemy 2.0** (async) + **Alembic**        |
| Database      | PostgreSQL + pgvector                           |
| AI            | LangChain (LLM + embeddings)                    |
| Search        | pgvector + keyword fallback                     |
| Cache / queue | Redis + ARQ                                     |
| Auth          | JWT + HttpOnly session cookie                   |

### Database — SQLAlchemy 2.0 + Alembic

| Layer | Location | Role |
| --- | --- | --- |
| **Models** | `infrastructure/database/models/` | SQLAlchemy 2.0 declarative models (`Mapped`, `mapped_column`, `relationship`) |
| **Repositories** | `infrastructure/database/repositories/` | Async queries via `AsyncSession` |
| **Session** | `core/database.py` | `create_async_engine` + `async_sessionmaker` (`asyncpg` driver) |
| **Migrations** | `alembic/` | Alembic revision scripts (`alembic/versions/`) |

**Workflow after changing a model:**

1. Edit model in `infrastructure/database/models/`
2. Generate migration: `alembic revision --autogenerate -m "describe change"`
3. Apply: `alembic upgrade head` (or Docker equivalent in [Quick start](#quick-start))

`init_db()` on startup runs `create_all` for local Docker convenience; **Alembic is the source of truth** for schema changes.

---

## Project structure

Clean architecture — dependencies point inward (API → application → domain ← infrastructure).

```
app/
├── api/v1/                    HTTP layer (routers + dto/)
│   ├── auth/
│   ├── chat/
│   ├── conversations/
│   ├── knowledge/             routes under /documents
│   └── health/
├── application/               Use-cases
│   ├── auth/                  service.py, mapper.py
│   ├── chat/                  service.py, helpers.py, mapper.py, stream_events.py
│   ├── conversations/
│   └── knowledge/
├── domain/                    Business rules and ports
│   └── chat/                  entities.py, ports.py
├── infrastructure/            External systems
│   ├── database/              SQLAlchemy 2.0 models + repositories
│   │   ├── models/            ORM (Mapped, mapped_column)
│   │   └── repositories/      AsyncSession data access
│   ├── llm/                   LLM adapters (implements LLMPort)
│   │   ├── factory.py         build_llm_port() — Demo vs LangChain
│   │   ├── errors.py          LLMProviderError (infrastructure)
│   │   ├── langchain/         LangChain adapter + message mapper
│   │   └── demo/              DemoProvider (offline mode)
│   ├── vectorstore/           embeddings + pgvector retrieval (implements RetrieverPort)
│   ├── cache/                 Redis, sessions
│   ├── queue/                 ARQ queue + worker
│   └── jobs/                  background tasks
└── core/                      Cross-cutting concerns
    ├── config.py
    ├── middleware.py          Request ID, CORS, security headers, IP rate limit
    ├── exceptions/            Stable JSON error envelope + handlers
    ├── dependencies.py        Depends(get_current_user), service wiring
    ├── security.py            JWT encode/decode (used by Depends, not middleware)
    └── database.py            SQLAlchemy 2.0 async engine + session factory
```

### Request flow

```
HTTP Request
    ↓
core/middleware.py     Request ID · CORS · security headers · IP rate limit
    ↓
api/v1/router.py       Validate input, call application service
    ↓
Depends(get_current_user)   Auth — session cookie or Bearer JWT
    ↓
application/service    Use-case (stream chat, upload document, …)
    ↓
domain/ports           LLMPort, RetrieverPort (interfaces)
    ↓
infrastructure/        Postgres, Redis, llm/, vectorstore/
```

**Rule:** Middleware handles **global HTTP** concerns only. Authentication and authorization live in `Depends(get_current_user)` — not in middleware.

### LLM and RAG architecture

**Dependency direction:**

```
API (router)
    ↓
Application (ChatService, helpers.py — prompt + RAG orchestration)
    ↓
LLMPort / RetrieverPort
    ↑
Infrastructure
    ├── DemoProvider          (no API key)
    └── LangChainProvider     (Gemini → fallback model → OpenAI)
            ↓
        LangChain → Gemini / OpenAI
```

| Component | Responsibility |
| --- | --- |
| `application/chat/helpers.py` | Build messages, fetch RAG context, strict/hybrid routing |
| `application/chat/stream_events.py` | Map internal events → SSE frames (`meta`, `token`, `done`, `error`) |
| `infrastructure/llm/langchain/provider.py` | Adapter only: `astream` / `ainvoke`, model fallback chain |
| `infrastructure/llm/demo/provider.py` | Canned replies when no API key |
| `infrastructure/llm/factory.py` | `build_llm_port()` — selects Demo vs LangChain |
| `infrastructure/llm/errors.py` | `LLMProviderError` — mapped to `LLMError` / SSE in application |

**LLM fallback chain** (when keys are set):

1. Primary provider (`GEMINI_MODEL` or OpenAI)
2. `GEMINI_FALLBACK_MODEL` (if set)
3. Cross-provider OpenAI (if key configured and primary is not OpenAI)
4. `LLMProviderError` → SSE `error` event or HTTP 502

**RAG retrieval** (`infrastructure/vectorstore/retriever.py`):

- Vector search with cosine distance threshold (`RAG_MAX_DISTANCE`)
- Keyword search
- Fallback chunks **only in hybrid mode** (`RAG_STRICT_MODE=false`)

| `RAG_STRICT_MODE` | No relevant KB hit |
| --- | --- |
| `true` | Refuse with fixed message — LLM not called |
| `false` | Fall back to LLM general knowledge |

**Rule:** Application code depends on **ports**, not LangChain directly. Adapters live in `infrastructure/llm/` and `infrastructure/vectorstore/`.

### Layer responsibilities

| Layer             | Responsibility                                            |
| ----------------- | --------------------------------------------------------- |
| `api/`            | Validate HTTP input, call services, return responses      |
| `application/`    | Use-cases: register user, stream chat, upload document    |
| `domain/`         | Core types and interfaces (`LLMPort`, `RetrieverPort`)    |
| `infrastructure/` | Postgres, Redis, LLM adapters, vector search, job worker |
| `core/`           | Config, middleware, exceptions, auth dependencies         |

**Rule:** Application code depends on **ports**, not LangChain directly. Adapters live in `infrastructure/llm/` and `infrastructure/vectorstore/`.

See [LLM and RAG architecture](#llm-and-rag-architecture) for provider fallback and strict RAG modes.

---

## API routes

Base path: `/api/v1`

### Health

| Method | Path      | Use                                                         |
| ------ | --------- | ----------------------------------------------------------- |
| `GET`  | `/health` | Status page — reports LLM, Postgres, Redis, and layer flags |

### Auth

| Method | Path             | Use                                                 |
| ------ | ---------------- | --------------------------------------------------- |
| `POST` | `/auth/register` | Sign-up form — create account and start a session   |
| `POST` | `/auth/login`    | Login form — authenticate and start a session       |
| `POST` | `/auth/logout`   | Logout button — revoke session and clear cookie     |
| `GET`  | `/auth/me`       | App boot — load current user profile for the header |

Protected routes accept **session cookie** first, then **Bearer JWT** as fallback.

### Conversations

| Method   | Path                  | Use                                         |
| -------- | --------------------- | ------------------------------------------- |
| `GET`    | `/conversations`      | Sidebar — list all chat threads             |
| `GET`    | `/conversations/{id}` | Open thread — load full message history     |
| `DELETE` | `/conversations/{id}` | Sidebar delete — remove thread and messages |

### Chat

| Method | Path             | Use                                               |
| ------ | ---------------- | ------------------------------------------------- |
| `POST` | `/chat/stream`   | Main chat UI — stream AI tokens via SSE           |
| `POST` | `/chat/complete` | Non-streaming clients — return full reply as JSON |

### Knowledge (documents)

| Method   | Path              | Use                                             |
| -------- | ----------------- | ----------------------------------------------- |
| `GET`    | `/documents`      | Knowledge page — list uploaded documents        |
| `POST`   | `/documents`      | Upload form — ingest text and enqueue embedding |
| `DELETE` | `/documents/{id}` | Remove document and vector chunks               |

Interactive docs: http://localhost:8000/docs

---

## Request flows

### Chat stream (main UI path)

```
POST /chat/stream
  → rate limit (Redis)
  → find or create conversation
  → save user message
  → fetch RAG context (optional; similarity threshold + strict/hybrid mode)
  → build LLM messages (application layer)
  → stream via LLMPort (SSE: meta → token → done, or error on LLM failure)
  → save assistant message
  → every 4 messages → enqueue conversation summary job
```

SSE events from `stream_events.py`:

| Event | Payload |
| --- | --- |
| `meta` | `conversation_id`, `llm`, `route` |
| `token` | `{ "content": "..." }` |
| `done` | `conversation_id`, `content`, `route`, `rag` |
| `error` | `{ "code": "LLM_ERROR", "message": "..." }` |

### Knowledge upload

```
POST /documents
  → save document row
  → split text into chunks
  → commit
  → ARQ job: embed chunks → store vectors in pgvector
```

Without an API key, chunks are saved and **keyword search** still works; embeddings stay empty.

### Background jobs (ARQ worker)

| Job                      | Trigger               | Action                                 |
| ------------------------ | --------------------- | -------------------------------------- |
| `process_document`       | After document upload | Embed chunks with LangChain → pgvector |
| `summarize_conversation` | Every 4 chat messages | LLM summary → `Conversation.summary`   |

Worker command: `arq app.infrastructure.queue.worker.WorkerSettings`

---

## Application services (key entry points)

| Service               | Method                | Endpoint                     |
| --------------------- | --------------------- | ---------------------------- |
| `AuthService`         | `register_user`       | `POST /auth/register`        |
| `AuthService`         | `login_user`          | `POST /auth/login`           |
| `AuthService`         | `get_user_profile`    | `GET /auth/me`               |
| `ChatService`         | `stream_chat`         | `POST /chat/stream`          |
| `ChatService`         | `complete_chat`       | `POST /chat/complete`        |
| `ConversationService` | `list_conversations`  | `GET /conversations`         |
| `ConversationService` | `get_conversation`    | `GET /conversations/{id}`    |
| `ConversationService` | `delete_conversation` | `DELETE /conversations/{id}` |
| `KnowledgeService`    | `list_documents`      | `GET /documents`             |
| `KnowledgeService`    | `create_document`     | `POST /documents`            |
| `KnowledgeService`    | `delete_document`     | `DELETE /documents/{id}`     |

Chat helpers (`application/chat/helpers.py`): `fetch_rag_context`, `generate_full_reply`, `generate_streaming_tokens`.

---

## Docker

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build
```

| Service    | Port | Role                             |
| ---------- | ---- | -------------------------------- |
| `api`      | 8000 | FastAPI (hot reload in dev)      |
| `worker`   | —    | ARQ background jobs              |
| `postgres` | 5432 | PostgreSQL + pgvector            |
| `redis`    | 6379 | Sessions, rate limits, job queue |
| `adminer`  | 8080 | Database admin UI                |

Start the UI separately: `cd ../frontend && npm run dev`

### Environment variables

Copy `.env.example` → `.env`. All keys match `app/core/config.py` (`Settings`).

| Variable | Default (Docker) | Purpose |
| --- | --- | --- |
| `APP_NAME` | `AI Chat` | API title (Swagger) |
| `APP_ENV` | `development` | `production` enables secure cookies |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed frontend origins (comma-separated) |
| `POSTGRES_USER` | `ai_chat` | Postgres user (compose + `DATABASE_URL`) |
| `POSTGRES_PASSWORD` | `ai_chat_pass` | Postgres password |
| `POSTGRES_DB` | `ai_chat` | Database name |
| `DATABASE_URL` | `@postgres:5432` | Async SQLAlchemy URL (`asyncpg`). Use `@localhost` for local Python |
| `REDIS_URL` | `redis://redis:6379/0` | Sessions, rate limits, ARQ queue. Use `localhost` for local Python |
| `GEMINI_API_KEY` | *(empty)* | Gemini LLM + embeddings (empty = demo mode) |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Gemini chat model (older models like `gemini-2.0-flash` return 404 for new keys) |
| `GEMINI_FALLBACK_MODEL` | *(empty)* | Secondary Gemini model when primary fails |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Gemini embedding model |
| `RAG_STRICT_MODE` | `false` | `true` = refuse when no relevant KB hit; `false` = hybrid (LLM fallback) |
| `RAG_MAX_DISTANCE` | `0.45` | Max pgvector cosine distance for a chunk to count as relevant |
| `JWT_SECRET_KEY` | *(dev placeholder)* | Sign access tokens (min 32 characters in production) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | `10080` (7 days) | Token / session lifetime |
| `RATE_LIMIT_PER_MINUTE` | `30` | Per-user chat rate limit |
| `RATE_LIMIT_IP_PER_MINUTE` | `120` | Per-IP global rate limit |
| `SESSION_COOKIE_NAME` | `session_id` | HttpOnly session cookie name |
| `COOKIE_SAMESITE` | `lax` | Cookie SameSite policy |

**LLM:** Set `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey). New keys use the `AQ.` auth-key format (older `AIza…` keys still work). Use `GEMINI_MODEL=gemini-3.6-flash`. If chat returns *permission denied* or *quota* errors, enable billing on the linked Google Cloud project. Leave `GEMINI_API_KEY` empty for **demo mode**.

Docker Compose overrides `DATABASE_URL` and `REDIS_URL` for `api` / `worker` services; values in `.env` still apply when running uvicorn on the host.

### Database migrations (SQLAlchemy 2.0 + Alembic)

Schema is defined in `infrastructure/database/models/` (SQLAlchemy 2.0). Versioned changes go through **Alembic** in `alembic/versions/`.

On first startup, `init_db()` creates extensions, tables, and indexes automatically (`create_all`). For reproducible schema changes, use Alembic.

#### Docker

```powershell
# --- Apply (upgrade) ---
docker compose run --rm api alembic upgrade head          # all pending
docker compose run --rm api alembic upgrade +1            # one step forward
docker compose run --rm api alembic upgrade 002_perf_indexes   # to specific revision

# --- Revert (downgrade) ---
docker compose run --rm api alembic downgrade -1          # undo last migration
docker compose run --rm api alembic downgrade -2          # undo last 2 migrations
docker compose run --rm api alembic downgrade 001_initial # to specific revision
docker compose run --rm api alembic downgrade base        # revert all migrations

# --- Create & inspect ---
docker compose run --rm api alembic revision --autogenerate -m "describe change"
docker compose run --rm api alembic revision -m "describe change"   # empty migration
docker compose run --rm api alembic current
docker compose run --rm api alembic history
docker compose run --rm api alembic history --verbose
docker compose run --rm api alembic stamp head            # mark DB at head without running SQL
```

#### Local (venv active, Postgres running)

```powershell
.\.venv\Scripts\Activate.ps1

# --- Apply (upgrade) ---
alembic upgrade head
alembic upgrade +1
alembic upgrade 002_perf_indexes

# --- Revert (downgrade) ---
alembic downgrade -1
alembic downgrade -2
alembic downgrade 001_initial
alembic downgrade base

# --- Create & inspect ---
alembic revision --autogenerate -m "describe change"
alembic revision -m "describe change"
alembic current
alembic history
alembic history --verbose
alembic stamp head
```

**Typical workflow after editing a model:**

1. Change `infrastructure/database/models/*.py`
2. `alembic revision --autogenerate -m "add column foo"`
3. Review the generated file in `alembic/versions/`
4. `alembic upgrade head`
5. To undo: `alembic downgrade -1`

Migration files:

| Revision           | File                  | Purpose                                                    |
| ------------------ | --------------------- | ---------------------------------------------------------- |
| `001_initial`      | `001_initial.py`      | Users, conversations, messages, documents, pgvector chunks |
| `002_perf_indexes` | `002_perf_indexes.py` | Composite indexes for chat and knowledge queries           |

**Note:** `create_all` on startup is idempotent for local Docker; Alembic is the source of truth when you change models and need reproducible upgrades.

---

## Dev tooling (Python + Pylance + Ruff)

**FastAPI + VS Code:** Python + Pylance + Ruff.

| Tool        | Responsibility                               |
| ----------- | -------------------------------------------- |
| **Pylance** | IntelliSense, type checking, Python analysis |
| **Ruff**    | Formatting, linting, import sorting          |

Install extensions (or accept workspace recommendations): **Python**, **Pylance**, **Ruff**.

Workspace settings: `.vscode/settings.json`  
Config: `backend/pyproject.toml` (`line-length = 88`, rules `E`, `F`, `I`, `UP`, `B`).

**Terminal (Ruff):**

```powershell
# From backend/
.\scripts\ruff.ps1
```

Or:

```powershell
ruff format .
ruff check . --fix
```

**Editor:** Pylance handles analysis in VS Code; Ruff formats and fixes on save.

---

## Tests

Three layers: **unit** (no DB), **integration** (Postgres), **e2e** (full stack).

```powershell
docker compose up -d --build

# All tests
docker compose run --rm api pytest

# By layer
docker compose run --rm api pytest -m unit
docker compose run --rm api pytest -m integration

# E2E against running stack
docker compose up -d
docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e
```

| Layer       | Folder                                    | What it covers                                  |
| ----------- | ----------------------------------------- | ----------------------------------------------- |
| Unit        | `tests/api`, `tests/ai`, `tests/services` | DTOs, mappers, RAG routing, JWT, rate limits    |
| Integration | `tests/integration/`                      | Auth, chat persistence, SSE contract, knowledge |
| E2E         | `tests/e2e/`                              | Register → chat → stream smoke tests            |

Full guide: [../docs/TESTING.md](../docs/TESTING.md)

---

## Security

Sessions, cookies, rate limits, and auth details: [../docs/SECURITY.md](../docs/SECURITY.md)

---

## Local development tips

1. **Demo mode** — leave `GEMINI_API_KEY` empty; API still streams and persists messages.
2. **Migrations** — see [Database migrations (SQLAlchemy 2.0 + Alembic)](#database-migrations-sqlalchemy-20--alembic) above.
3. **Logs** — `docker compose logs -f api worker`
4. **Reset data** — `docker compose down -v` (removes volumes)
