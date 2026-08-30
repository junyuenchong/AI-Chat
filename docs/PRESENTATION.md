# Presentation script (15–20 minutes)

**Assignment:** Question 2 — streaming LLM chat  
**Project:** AI Chat — FastAPI SSE + Next.js + Postgres + LangChain  
**Goal:** Token-by-token streaming with conversation history in the database.

---

## Slide 1 — Title (30 sec)

> "I chose **Question 2** and built a minimal production-style chat: FastAPI streams LLM tokens over SSE, Postgres stores conversation history, and Next.js is the UI. LangChain lives in infrastructure only — the application layer depends on ports, not the framework."

---

## Slide 2 — Why Question 2 (not 1 or 3) (1.5 min)

| | **Q1: Agentic RAG** | **Q2: LLM chat (this project)** | **Q3: Agentic AI** |
| --- | --- | --- | --- |
| **Primary goal** | Retrieve chunks; agent decides retrieval | Stream tokens; LLM remembers prior turns | Autonomous tool-use against external systems |
| **What I built** | Not in scope | `POST /chat/stream`, SSE, Postgres, JWT, Next.js, Docker, tests | Not in scope |
| **LangChain use** | Retriever + embeddings + agent | Chat Model + Messages + `astream()` | LangGraph + tools |

> "Focus is **streaming + session memory** — not agentic RAG or agentic AI."

---

## Slide 3 — Problem & goals (1 min)

- User sees **tokens appear live** (SSE).
- LLM **remembers prior turns** (Postgres — not LangChain Memory).
- **Demo mode** without API keys (HTTP, DB, SSE still real).
- **Clean Architecture** + unit / integration / e2e tests.

---

## Slide 4 — Architecture (2 min)

```
Next.js → FastAPI → ChatService → Postgres (history) + LangChain (LLM only)
```

```
┌──────────────┐     ┌────────────────────┐
│  PostgreSQL  │     │     LangChain      │
│  conversations│    │  Chat Model        │
│  messages    │     │  Messages          │
│              │     │  astream()         │
└──────────────┘     └────────────────────┘
```

**Postgres = persistence. LangChain = LLM interaction only.**

LangChain folder:

```
infrastructure/ai/langchain/
├── llm/        factory, provider, messages
├── prompts/    SYSTEM_PROMPT (plain string)
├── chains/     ChatChain
├── callbacks/  stream_llm_tokens
└── adapters/   build_chat_engine()
```

**Not used:** Vector DB · Retriever · Embeddings · RAG · LangGraph · Agent · Tools · LangChain Memory

---

## Slide 5 — LangChain components (1 min)

Only three — keep it simple:

| Component | What it does |
| --- | --- |
| **Chat Model** | `ChatGoogleGenerativeAI` or `ChatOpenAI` |
| **Messages** | `SystemMessage` + history as `HumanMessage`/`AIMessage` |
| **Streaming** | `async for chunk in llm.astream(messages)` |

```python
messages = [
    SystemMessage(content=SYSTEM_PROMPT),
    *history_from_postgres,
    HumanMessage(content=user_message),
]
async for chunk in llm.astream(messages):
    yield chunk.content   # → SSE token events
```

No `ChatPromptTemplate`. History comes from Postgres.

---

## Slide 6 — Streaming flow (1 min)

1. `POST /api/v1/chat/stream`
2. Save user message → load history from Postgres
3. Build LangChain messages → `llm.astream()`
4. SSE: `meta` → `token`… → `done`
5. Save assistant reply to Postgres

---

## Slide 7 — Live demo (5 min)

```powershell
cd backend
docker compose down -v --remove-orphans
docker compose up --build
docker compose run --rm api alembic upgrade head
docker compose run --rm api python alembic/seeds/run.py
cd ../frontend && npm run dev
```

1. Login `demo@example.com` / `demo123` (or Register a new account first)
2. Send a message → show tokens streaming live
3. Follow-up → show session memory (same `conversation_id`)
4. Optional: Adminer → `messages` table
5. Optional: set `GEMINI_API_KEY` → real LLM

---

## Slide 8 — Code walk (1.5 min)

| Layer | File |
| --- | --- |
| Router | `api/v1/chat/router.py` |
| Service | `application/chat/service.py` |
| Port | `domain/chat/ports.py` (`ChatEngine`, `LLMPort`) |
| Chain | `infrastructure/ai/langchain/chains/chat_chain.py` |
| LLM | `infrastructure/ai/langchain/llm/provider.py` (`astream`) |
| Frontend SSE | `frontend/src/lib/sse/reader.ts` |

---

## Slide 9 — Testing & Docker (2 min)

```powershell
docker compose run --rm api pytest    # 51 tests, demo mode
cd frontend && npm test               # 41 tests
```

Stack: **Postgres + API** only (no Redis, worker, vector DB).

Pytest clears API keys — tests never hit external LLMs.

---

## Slide 10 — Q&A prep

1. _Why Q2?_ — Streaming API + DB session memory.
2. _Why not Q1/Q3?_ — No retrieval agent, no tool loop, no LangGraph.
3. _Why Postgres not LangChain Memory?_ — Persistence is app responsibility; LangChain only calls the model.
4. _Why SessionLocal in stream?_ — Request DB closes before SSE ends.
5. _Why LangChain in infrastructure?_ — `ChatEngine` port keeps app layer swappable.
6. _Why JWT not cookies?_ — Simpler Q2 stack; token in `sessionStorage`.
7. _Why not LangGraph?_ — Q2 is a straight line (history → LLM → stream), not a multi-step agent graph.

---

## One-line close

> "Question 2: FastAPI streams LangChain tokens over SSE, Postgres gives the LLM memory, and tests cover unit logic through live smoke — Postgres + API in Docker."
