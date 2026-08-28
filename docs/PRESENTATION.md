# Presentation script — Question 2 (15–20 minutes)

**Project:** AI Chat — FastAPI SSE streaming + Next.js + Postgres session memory  
**Assignment:** Build a simple LLM chat interface with token streaming and DB session history.

---

## Slide 1 — Title (30 sec)

> "I built a full-stack streaming chat: FastAPI streams LLM tokens over SSE, Postgres stores conversation history, and Next.js is the UI. LangChain handles model calls only — retrieval and persistence are custom app code."

---

## Slide 2 — Problem & goals (1 min)

**Say:**

- User sends a message and sees **tokens appear live** (not wait for full JSON).
- LLM must **remember prior turns** in the same session.
- Stack must be **demo-able** without a paid API key (demo mode).
- **Bonus:** Docker, friendly UI, tests at unit / integration / e2e levels.

**Show:** assignment checklist on screen — tick Q2 items.

---

## Slide 3 — Architecture (2 min)

**Diagram to draw / show:**

```
Next.js UI
   │  JSON → /api/v1 proxy
   │  SSE  → FastAPI direct (no proxy buffering)
   ▼
FastAPI api/v1
   ▼
services/chat.py
   ├─ Redis rate limit
   ├─ Postgres: Conversation + Message
   ├─ ai/chat.py: optional RAG → LangChain LLM
   └─ ARQ jobs: summarize / embed (async)
```

**Key sentence:**

> "API layer is thin. Business logic lives in services. AI logic is isolated under `ai/`."

---

## Slide 4 — LangChain vs RAG vs app (1 min)

| Layer | Uses LangChain? | Example |
| --- | --- | --- |
| LLM stream / complete | Yes | `ai/llm/providers.py` |
| Embeddings | Yes | `ai/rag/embeddings.py` |
| Chunk + search | No | Python + pgvector SQL |
| HTTP / auth / DB | No | FastAPI + SQLAlchemy |

> "This is **traditional RAG**, not agentic RAG — one retrieve pass, then generate."

---

## Slide 5 — Live demo part 1: Auth + chat (4 min)

**Steps:**

1. `docker compose up --build` (backend) + `npm run dev` (frontend)
2. Open http://localhost:3000
3. **Register** → explain HttpOnly session cookie (Redis-backed, not localStorage)
4. Send: *"What is the difference between LangChain and RAG?"*
5. Point at **tokens streaming** in the UI
6. Open http://localhost:8000/docs → show `POST /api/v1/chat/stream`

**Call out:**

- SSE events: `meta` → many `token` → `done`
- User message saved **before** stream starts (durable history)

---

## Slide 6 — Live demo part 2: Session memory (2 min)

**Steps:**

1. Ask a follow-up: *"Summarize what I just asked."*
2. Refresh the page → login → open same conversation in sidebar
3. Show messages still there (Postgres)
4. Optional: Adminer http://localhost:8080 → `messages` table

**Say:**

> "History is loaded from `messages` ordered by `created_at`, last 12 turns passed to LangChain message builder."

---

## Slide 7 — Live demo part 3: Knowledge + RAG (2 min, optional)

1. Upload document text: *"Annual leave is 14 days."*
2. Ask: *"How many annual leave days?"*
3. Mention `use_rag: true` → retriever → context appended to system prompt

**If demo mode (no API key):**

> "Demo mode still exercises retrieve + SSE; LLM text is mocked but the pipeline is real."

---

## Slide 8 — SSE implementation (2 min)

**Code pointers:**

- `api/v1/chat/router.py` — `EventSourceResponse`
- `services/chat.py` — dedicated `SessionLocal()` (SSE outlives request DB session)
- `frontend/lib/api.ts` — `streamUrl()` hits FastAPI directly

**Why not browser EventSource?**

> "EventSource is GET-only. We need POST + JWT, so we use `fetch` + readable stream."

---

## Slide 9 — Testing methodology (2 min)

**Three layers:**

| Layer | Command | Chat scenarios covered |
| --- | --- | --- |
| **Unit** | `pytest -m unit` | RAG routing, stream event order, rate limit, DTOs |
| **Integration** | `docker compose run --rm api pytest -m integration` | JWT, multi-turn, SSE contract, 404, 429 |
| **E2E** | `E2E_BASE_URL=... pytest -m e2e` | Live register → complete → stream |

**Say:**

> "Chat tests follow production: same JWT, same SSE meta/token/done events, Postgres persistence, and rate-limit code path with a fake Redis in integration tests."

---

## Slide 10 — Docker & ops (1 min)

| Service | Role |
| --- | --- |
| `api` | uvicorn |
| `worker` | ARQ summarize + embed |
| `postgres` | pgvector |
| `redis` | rate limit + queue |

Health: `GET /api/v1/health` — fail soft per dependency.

---

## Slide 11 — Q&A prep (1 min buffer)

**Expected questions:**

1. *Why SessionLocal in stream?* — Request-scoped DB closes before SSE finishes.
2. *Why LangChain?* — Provider abstraction + message types; not used for retrieval.
3. *How test without API key?* — Demo mode in `providers.py`; retrieve tested with mocks + integration.
4. *Agentic RAG?* — Out of scope; this is retrieve-then-generate.
5. *Scale?* — Rate limit Redis, async ARQ, pgvector index in production.

---

## Timing cheat sheet

| Section | Minutes |
| --- | --- |
| Intro + architecture | 4 |
| Live demo | 8 |
| SSE + code walk | 2 |
| Testing + Docker | 3 |
| Q&A | 3 |
| **Total** | **~20** |

---

## One-line close

> "FastAPI streams LangChain tokens over SSE, Postgres gives the LLM memory, and tests cover unit logic, integrated APIs, and live smoke — all in Docker."
