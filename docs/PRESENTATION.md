# Presentation script (15–20 minutes)

**Project:** AI Chat — FastAPI SSE streaming + Next.js + Postgres session memory + RAG  
**Goal:** Streaming LLM chat with conversation history stored in the database.

---

## Slide 1 — Title (30 sec)

> "I built a full-stack streaming chat: FastAPI streams LLM tokens over SSE, Postgres stores conversation history, and Next.js is the UI. LangChain lives in infrastructure only — the application layer depends on ports, not the framework."

---

## Slide 2 — Problem & goals (1 min)

**Say:**

- User sends a message and sees **tokens appear live** (not wait for full JSON).
- LLM must **remember prior turns** in the same session.
- Stack must be **demo-able** without a paid API key (demo mode).
- **Bonus:** Docker, clean architecture, tests at unit / integration / e2e levels.

---

## Slide 3 — Architecture (2 min)

**Diagram:**

```
Next.js UI
   │  JSON → /api/v1 proxy (cookies)
   │  SSE  → FastAPI direct (no proxy buffering)
   ▼
api/v1/router.py + dto/request.py
   ▼
application/*/mapper.py → application/*/service.py
   ▼
domain/entities.py + ports.py (ChatEngine)
   ▼
infrastructure/
   ├─ ai/langchain/     LLM, RAG, agent (5 files)
   ├─ database/         Postgres + repositories
   ├─ vector/           pgvector queries
   ├─ cache/redis.py    sessions + rate limits
   └─ messaging/        ARQ embed + summarize jobs
```

**Key sentence:**

> "API handles HTTP and DTOs. Application handles use cases. Domain holds ports. Infrastructure implements LangChain, Postgres, Redis, and pgvector."

---

## Slide 4 — LangChain vs RAG vs app (1 min)

| Layer | Uses LangChain? | Path |
| --- | --- | --- |
| LLM stream / complete | Yes | `infrastructure/ai/langchain/llm.py` |
| Embeddings | Yes | `infrastructure/ai/langchain/llm.py` |
| Prompts | Yes | `infrastructure/ai/langchain/prompts.py` |
| RAG retrieval | Partial | `infrastructure/ai/langchain/retrieval.py` + `infrastructure/vector/pgvector.py` |
| Orchestration | Yes | `infrastructure/ai/langchain/agent.py` (`ChatAgent` implements `ChatEngine`) |
| HTTP / auth / DB | No | FastAPI + SQLAlchemy |

> "Traditional RAG — retrieve context, then generate. Not agentic RAG."

---

## Slide 5 — Live demo part 1: Setup + auth + chat (4 min)

**Steps:**

```powershell
cd backend
docker compose up --build
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py

cd ../frontend && npm run dev
```

1. Open http://localhost:3000
2. **Login** with `demo@example.com` / `demo123` (or register)
3. Explain HttpOnly session cookie (`infrastructure/cache/redis.py`, not localStorage)
4. Send: _"What is the difference between LangChain and RAG?"_
5. Point at **tokens streaming** in the UI
6. Open http://localhost:8000/docs → `POST /api/v1/chat/stream`

**Call out:**

- SSE events: `meta` → many `token` → `done`
- User message saved **before** stream starts

---

## Slide 6 — Live demo part 2: Session memory (2 min)

**Steps:**

1. Follow-up: _"Summarize what I just asked."_
2. Refresh → login → same conversation in sidebar
3. Optional: Adminer http://localhost:8080 → `messages` table

> "History loads from `messages` ordered by `created_at`, passed to the LLM via the chat agent."

---

## Slide 7 — Live demo part 3: Knowledge + RAG (2 min)

Seeded docs include `hr-policy.md` (14 days annual leave).

1. Ask: _"How many annual leave days do we get?"_
2. Mention `use_rag: true` → retriever → context in system prompt

**Upload flow:**

```
POST /documents → chunk → ARQ job → embed → pgvector
```

**Demo mode (no API key):**

> "Demo mode mocks LLM text but the full HTTP, DB, SSE, and keyword-search pipeline still runs."

---

## Slide 8 — Clean architecture walk (2 min)

**Code pointers:**

| Layer | Example |
| --- | --- |
| Router | `api/v1/chat/router.py` — thin HTTP adapter |
| DTO | `api/v1/chat/dto/request.py`, `response.py` |
| Mapper | `application/chat/mapper.py` — DTO ↔ command/result |
| Service | `application/chat/service.py` — no LangChain imports |
| Port | `domain/chat/ports.py` — `ChatEngine` |
| Infrastructure | `infrastructure/ai/langchain/agent.py` |

**SSE specifics:**

- `api/v1/chat/router.py` — `EventSourceResponse`
- `application/chat/service.py` — own `SessionLocal()` (SSE outlives request DB session)
- `frontend/src/lib/sse/reader.ts` — parses events

> "EventSource is GET-only. We use `fetch` + readable stream for POST + auth."

---

## Slide 9 — Database migrations & seeds (1 min)

| | Path |
| --- | --- |
| Schema | `app/infrastructure/database/models.py` |
| Migrations | `alembic/versions/` (`001` users → `002` conversations → `003` documents) |
| Seeds | `alembic/seeds/` (`users.py`, `documents.py`, `run.py`) |

```powershell
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
```

> "Schema migrations and reference data are separated — Alembic `versions/` for DDL, `seeds/` for demo data."

---

## Slide 10 — Testing & quality (2 min)

### Backend

| Layer | Command | Covers |
| --- | --- | --- |
| **Unit** | `pytest -m unit` | Mappers, RAG routing, rate limit, DTOs |
| **Integration** | `pytest -m integration` | JWT, multi-turn, SSE, 404, 429 |
| **E2E** | `pytest -m e2e` | Live register → chat → stream |
| **Format + lint** | `.\scripts\ruff.ps1` | Ruff |

### Frontend

| Tool | Command |
| --- | --- |
| TypeScript | `npm run typecheck` |
| ESLint | `npm run lint` |
| Prettier | `npm run format:check` |
| Jest | `npm test` |
| Playwright | `npm run test:e2e` |

Details: [TESTING.md](TESTING.md)

---

## Slide 11 — Docker & ops (1 min)

| Service | Role |
| --- | --- |
| `api` | Uvicorn |
| `worker` | ARQ — embed + summarize |
| `postgres` | pgvector |
| `redis` | sessions, rate limits, job queue |
| `adminer` | DB UI |

| Folder | Purpose |
| --- | --- |
| `infrastructure/database/` | PostgreSQL |
| `infrastructure/vector/` | pgvector queries |
| `infrastructure/cache/` | Redis sessions + rate limits |
| `infrastructure/messaging/` | ARQ queue + worker |
| `infrastructure/ai/langchain/` | LangChain (5 files) |

Health: `GET /api/v1/health`

---

## Slide 12 — Q&A prep

1. _Why SessionLocal in stream?_ — Request-scoped DB closes before SSE finishes.
2. _Why LangChain in infrastructure?_ — Replaceable; application depends on `ChatEngine` port only.
3. _How test without API key?_ — Demo mode in `llm.py`; retriever tested with mocks.
4. _DTO vs entity vs ORM?_ — API DTO → mapper → service → domain → infrastructure ORM.
5. _Why separate cache/ and messaging/?_ — Same Redis, different responsibilities.
6. _Migrations vs seeds?_ — `alembic/versions/` = schema; `alembic/seeds/` = reference data.
7. _Frontend quality stack?_ — TypeScript strict + ESLint + Prettier + Jest + Playwright.

---

## Timing

| Section | Minutes |
| --- | --- |
| Intro + architecture | 4 |
| Live demo | 8 |
| Architecture + DB | 3 |
| Testing + Docker | 3 |
| Q&A | 2 |
| **Total** | **~20** |

---

## One-line close

> "FastAPI streams LangChain tokens over SSE, Postgres gives the LLM memory, clean layers keep LangChain swappable, and tests cover unit logic through live smoke — all in Docker."
