# FastAPI Backend (Question 2)

REST API for **streaming LLM chat** with Postgres conversation history and JWT authentication.

Runs in **Docker** (recommended) or locally with Python + Uvicorn. **Postgres only** — no Redis, worker, vector DB, RAG, or LangGraph.

---

## Quick start

### Docker (recommended)

```powershell
cd backend
Copy-Item .env.example .env
docker compose down -v --remove-orphans   # optional — fresh DB
docker compose up --build

# New terminal — after Postgres is healthy
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

Frontend: `cd ../frontend && npm install && npm run dev`

### Local Python

Requires **Python 3.12+**. Postgres runs in Docker.

```powershell
cd backend
Copy-Item .env.example .env
docker compose up postgres -d

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python alembic/seeds/run.py

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For local Python, set `DATABASE_URL` to `@localhost:5432` in `.env`.

### URLs

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| Adminer | http://localhost:8080 |

**Demo login:** `demo@example.com` / `demo123` (from seeds)

**New email?** Use `POST /auth/register` — login does not create accounts.

Leave `GEMINI_API_KEY` and `OPENAI_API_KEY` empty for **demo mode** (real HTTP, DB, SSE; mock LLM text).

### Common commands

```powershell
docker compose logs -f api
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
docker compose run --rm api pytest              # 51 tests
.\scripts\ruff.ps1
docker compose down -v --remove-orphans         # reset DB volumes
```

---

## Stack

| Component | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Database | PostgreSQL 16 |
| AI | LangChain — Chat Model + Messages + `astream()` |
| Auth | JWT (Bearer token) |

---

## LangChain (Q2 minimal)

Only three LangChain concepts are used. Everything else stays in application/domain code.

| LangChain component | Role | File |
| --- | --- | --- |
| **Chat Model** | `ChatGoogleGenerativeAI` / `ChatOpenAI` | `llm/factory.py` |
| **Messages** | `SystemMessage`, `HumanMessage`, `AIMessage` | `llm/messages.py` |
| **Streaming** | `llm.astream(messages)` | `llm/provider.py` |

**Not used:** `ChatPromptTemplate` · Retriever · Embeddings · RAG · LangGraph · Agent · Tools · LangChain Memory

Postgres stores history. LangChain only formats messages and calls the model.

### Request flow

```
api/v1/chat/router.py
  → application/chat/service.py
  → domain/chat/ports.py (ChatEngine)
  → infrastructure/ai/langchain/chains/chat_chain.py
  → infrastructure/ai/langchain/llm/provider.py
  → llm.astream()
```

### Project structure

```
backend/app/
├── core/           config, security, middleware, dependencies
├── api/v1/         routers + dto
├── application/    chat, auth, conversations services
├── domain/         entities + ports
├── shared/         retry helpers
└── infrastructure/
    ├── database/   models, repositories, session
    └── ai/langchain/
        ├── llm/        factory, provider, messages
        ├── prompts/    SYSTEM_PROMPT string
        ├── chains/     ChatChain
        ├── callbacks/  stream_llm_tokens
        └── adapters/   build_chat_engine()
```

| File | Role |
| --- | --- |
| `application/chat/service.py` | Save message, load history, SSE framing |
| `domain/chat/ports.py` | `ChatEngine` + `LLMPort` interfaces |
| `chains/chat_chain.py` | Build messages → call LLM |
| `llm/provider.py` | `astream` / `ainvoke`, retry, demo mode |
| `shared/retry.py` | Exponential backoff for transient errors |

### Chat flow

```
POST /chat/stream → save message → load history → ChatChain → astream() → SSE tokens → save reply
```

---

## Code comments

Every main module follows the same pattern (see `application/auth/service.py`):

| Element | Example |
| --- | --- |
| Module docstring | Request path — which router/service calls this file |
| Boxed block | `# ── function_name` with Path, Endpoint, Use |
| Inline steps | `# Step 1 — load user from Postgres` |

Routers, services, repositories, LangChain adapters, and `core/dependencies.py` are all commented this way.

---

## Database migrations & seeds

| | Path |
| --- | --- |
| Schema | `app/infrastructure/database/models.py` |
| Migrations | `alembic/versions/` |
| Seeds | `alembic/seeds/` |

| Revision | File | Creates |
| --- | --- | --- |
| `001_create_users` | `001_create_users.py` | `uuid-ossp` extension + `users` |
| `002_create_conversations` | `002_create_conversations.py` | `conversations`, `messages` |

### Migrations

Run from `backend/`.

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Apply all | `docker compose run --rm api alembic upgrade head` | `alembic upgrade head` |
| Revert last | `docker compose run --rm api alembic downgrade -1` | `alembic downgrade -1` |
| Current revision | `docker compose run --rm api alembic current` | `alembic current` |
| New migration | `docker compose run --rm api alembic revision --autogenerate -m "msg"` | `alembic revision --autogenerate -m "msg"` |

After editing `models.py`: autogenerate → review `alembic/versions/` → `upgrade head`.

If tables exist but Alembic was never run, reset with `docker compose down -v`.

### Seeds

| Action | Docker | Local (venv) |
| --- | --- | --- |
| Seed demo data | `docker compose run --rm api python alembic/seeds/run.py` | `python alembic/seeds/run.py` |

| Seed file | Data |
| --- | --- |
| `alembic/seeds/users.py` | Demo user + starter conversation |
| `alembic/seeds/run.py` | Orchestrator |

Idempotent — safe to re-run.

---

## API routes

Base path: `/api/v1`. Swagger: http://localhost:8000/docs

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/health` | Postgres + LLM status |
| `POST` | `/auth/register` | Create account → JWT |
| `POST` | `/auth/login` | Log in → JWT |
| `POST` | `/auth/logout` | No-op (stateless JWT) |
| `GET` | `/auth/me` | Current user (Bearer) |
| `GET` | `/conversations` | List threads |
| `GET` | `/conversations/{id}` | Load thread + messages |
| `DELETE` | `/conversations/{id}` | Delete thread |
| `POST` | `/chat/stream` | Stream reply (SSE) |
| `POST` | `/chat/complete` | Full reply (JSON) |

### SSE events

| Event | Payload |
| --- | --- |
| `meta` | `conversation_id`, `llm`, `route`, `components` |
| `token` | `{ "content": "..." }` |
| `done` | `conversation_id`, `content` |
| `error` | `{ "code", "message" }` |

---

## Docker services

| Service | Port | Role |
| --- | --- | --- |
| `api` | 8000 | FastAPI (hot-reload via volume mount) |
| `postgres` | 5432 | PostgreSQL 16 |
| `adminer` | 8080 | DB admin UI |

`docker-compose.yml` mounts `./app`, `./tests`, and `./alembic` for live dev.

---

## Environment variables

Copy `.env.example` → `.env`. All keys in `app/core/config.py`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `@postgres:5432` | Use `@localhost` for local Python |
| `GEMINI_API_KEY` | _(empty)_ | Gemini LLM; empty = try OpenAI or demo |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Primary chat model |
| `GEMINI_FALLBACK_MODEL` | _(empty)_ | Secondary Gemini model on primary failure |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI when Gemini key is empty |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `LLM_RETRY_MAX_ATTEMPTS` | `3` | Retries per model on transient errors |
| `LLM_RETRY_BASE_DELAY_SECONDS` | `0.5` | Initial backoff between retries |
| `LLM_RETRY_MAX_DELAY_SECONDS` | `8.0` | Max backoff cap |
| `JWT_SECRET_KEY` | _(dev)_ | Token signing (min 32 chars in production) |
| `JWT_EXPIRE_MINUTES` | `10080` | Token lifetime (7 days) |
| `CORS_ORIGINS` | `localhost:3000` | Allowed frontend origins |

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

Pytest **clears LLM API keys** in `tests/conftest.py` so all **51 tests** run in demo mode (no external API calls).

| Action | Docker | Local (venv) |
| --- | --- | --- |
| All tests | `docker compose run --rm api pytest` | `pytest` |
| Unit only | `docker compose run --rm api pytest -m unit` | `pytest -m unit` |
| Integration | `docker compose run --rm api pytest -m integration` | `pytest -m integration` |
| E2E | `docker compose run --rm -e E2E_BASE_URL=http://api:8000 api pytest -m e2e` | `pytest -m e2e` |

| Layer | Folder | Covers |
| --- | --- | --- |
| Unit | `tests/unit/` | DTOs, mappers, chat chain, retry, LLM failover, JWT |
| Integration | `tests/integration/` | Auth, chat, SSE, health |
| E2E | `tests/e2e/` | Register → chat → stream smoke |

### Format & lint — Ruff

| Action | Command |
| --- | --- |
| Format + lint (recommended) | `.\scripts\ruff.ps1` |
| Format only | `ruff format .` |
| Lint + auto-fix | `ruff check . --fix` |

Config: `pyproject.toml` · Install: `pip install -r requirements-dev.txt`

---

## Security

[../docs/SECURITY.md](../docs/SECURITY.md) — JWT auth, errors, production checklist.

---

## Related docs

| Document | Contents |
| --- | --- |
| [../README.md](../README.md) | Project overview |
| [../frontend/README.md](../frontend/README.md) | Next.js UI, SSE, Jest |
| [../docs/TESTING.md](../docs/TESTING.md) | Test strategy |
| [../docs/PRESENTATION.md](../docs/PRESENTATION.md) | Demo script |
