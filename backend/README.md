# FastAPI backend

Production-oriented AI chat API. Docker lives here. The Next.js UI is in `../frontend` (npm, not Docker).

**Stack today:** FastAPI + LangChain RAG chat (`ai/chat.py`) + Postgres/pgvector + Redis/ARQ.  
**Not used:** LangGraph, n8n.

## Architecture (easy to navigate)

| Folder        | Role                                           |
| ------------- | ---------------------------------------------- |
| **api/**      | HTTP: routers, DTOs, mapping                   |
| **core/**     | Config, security, errors, JWT dependencies     |
| **models/**   | Database tables (SQLAlchemy)                   |
| **db/**       | Database session + SQL access                  |
| **services/** | Business logic (use cases)                     |
| **ai/**       | LangChain + RAG chat (llm, prompts, rag, chat) |
| **clients/**  | External systems: Redis, ARQ                   |
| **jobs/**     | Background jobs (summary, embeddings)          |

**Rules:**

- FastAPI = HTTP. Service = business logic. AI = AI logic. `db/` = persistence.
- LangChain: `ai/llm`, `ai/prompts`, `ai/rag` (chunk + embed + retrieve).
- Chat AI flow: `ai/chat.py` (optional retrieve → LLM stream/complete).
- Chat streaming uses **SSE** (`POST /api/v1/chat/stream`).

## Domain glossary (read this first)

**Conversation** is the user's chat history.  
**Knowledge** is the information the AI can retrieve from.

| Term             | Meaning                                  | In this codebase                                    |
| ---------------- | ---------------------------------------- | --------------------------------------------------- |
| **Conversation** | Chat history (one thread)                | `models/conversation.py`, `/api/v1/conversations`   |
| **Message**      | Individual chat turn (user or assistant) | `models/message.py`                                 |
| **Chat**         | AI interaction (send prompt → get reply) | `services/chat.py`, `/api/v1/chat/stream\|complete` |
| **Knowledge**    | AI knowledge base                        | `services/knowledge.py`, `/api/v1/documents`        |
| **Document**     | Uploaded / source file                   | `models/document.py`                                |
| **Chunk**        | Split document content                   | `DocumentChunk` in `models/document.py`             |
| **Retriever**    | Finds relevant knowledge for a query     | `ai/rag/retrieve.py`                                |
| **RAG**          | Combines retrieved knowledge + LLM       | `ai/rag/` + `ai/chat.py`                            |

### Example

User asks: *"What is our company's annual leave policy?"*

```
Conversation                          Knowledge
└── Message                           └── company_handbook.pdf  (Document)
      └── User: What is our company's       ├── Chunk 1
          annual leave policy?              ├── Chunk 2  ← relevant (Retriever)
                                            └── Chunk 3
```

Request path:

```
Conversation
   ↓
Chat API          (/api/v1/chat/stream)
   ↓
ai/chat.py        (optional RAG → LLM)
   ↓
Retriever         (ai/rag/retrieve.py)
   ↓
Knowledge / Vector Store   (documents + pgvector chunks)
   ↓
RAG               (retrieved chunks + prompt)
   ↓
LLM               (ai/llm)
   ↓
Assistant Message (saved into the same Conversation)
```

```
Knowledge → Document → Chunk
Chat → Conversation → Message
RAG = Retriever(Chunks) + LLM
```

## Backend layout

```
app/
  main.py

  api/v1/                     # HTTP only
    router.py
    auth/     router.py dto.py mapping.py
    chat/
    conversations/
    knowledge/
    health/

  core/                       # shared config + security
    config.py security.py errors.py exceptions.py
    logging.py dependencies.py

  models/                     # ORM tables
    user.py conversation.py message.py document.py

  db/                         # SQL access
    session.py user.py conversation.py message.py document.py

  services/                   # business logic
    auth.py chat.py conversation.py knowledge.py

  ai/
    llm/                      # which LLM? stream / complete
    prompts/                  # what to tell the LLM
    rag/                      # chunk + embeddings + pgvector + retrieve
    chat.py                   # optional RAG → LLM (stream / complete)

  clients/                    # Redis, ARQ queue
  jobs/                       # ARQ worker + tasks
```

### `ai/chat.py` — Chat AI flow

```
use_rag?
  yes → Retriever (Knowledge / Chunks) → rag_context
  no  → skip
       ↓
LLM stream (SSE) or complete (JSON)
```

| Function      | Used by               | Job                                      |
| ------------- | --------------------- | ---------------------------------------- |
| `stream_chat` | `POST /chat/stream`   | retrieve → yield route/rag/token for SSE |
| `run_chat`    | `POST /chat/complete` | retrieve → one LLM answer                |

## Full workflow (end to end)

| Layer          | Role                                     | Where                          |
| -------------- | ---------------------------------------- | ------------------------------ |
| **LangChain**  | AI components (LLM, prompts, embeddings) | `app/ai/llm`, `prompts`, `rag` |
| **RAG / chat** | Retriever + Knowledge + LLM              | `app/ai/chat.py`, `ai/rag/`    |

```
Next.js UI
    │  JWT + HTTP
    ▼
FastAPI (api/v1)
    │
    ├─ Auth / Conversations / Knowledge  →  services → db/ → Postgres
    │
    └─ Chat (SSE or JSON)
           │
           ▼
      services/chat.py
           │
           ├─ Redis rate limit (clients/redis)
           ├─ Persist user message (db/ → Postgres)
           ├─ ai/chat.py  (optional retrieve → LLM stream/complete)
           ├─ Persist assistant message
           └─ ARQ enqueue (jobs/) when needed
```

### 1. Auth

```
POST /api/v1/auth/register|login
       ↓
api/v1/auth/router.py  (RegisterRequest / LoginRequest)
       ↓
services/auth.py
       ↓
db/user.py  →  models/user.py
       ↓
mapping.py → TokenResponse  (JWT access_token)
```

Protected routes use `core/dependencies.py` → `get_current_user` (Bearer JWT).

### 2. Knowledge ingest (RAG data)

```
POST /api/v1/documents
       ↓
api/v1/knowledge/router.py  (CreateDocumentRequest)
       ↓
services/knowledge.py
       ├─ save Document
       ├─ ai/rag/service.py  split_text() → DocumentChunk rows
       ├─ commit Postgres
       └─ ARQ enqueue process_document
              ↓
         jobs/tasks.py
              ├─ embeddings (Gemini / OpenAI)
              └─ replace chunks + vectors (pgvector)
```

Without an API key, chunks still store for **keyword** RAG; embeddings stay null.

### 3. Chat stream (SSE) — main path

Endpoint: `POST /api/v1/chat/stream`  
Library: `sse_starlette.EventSourceResponse`  
UI: `fetch` + read `text/event-stream` (POST + JWT; not browser `EventSource`).

```
Client POST /api/v1/chat/stream  { message, conversation_id?, use_rag }
       ↓
api/v1/chat/router.py
       ↓
services/chat.py  stream_chat()
       │
       ├─ 1. Redis rate limit
       ├─ 2. Open SessionLocal()   # SSE outlives request-scoped get_db()
       ├─ 3. get_or_create conversation
       ├─ 4. load history + save user message + commit
       ├─ 5. stream_chat()  (ai/chat.py → retrieve + LLM stream)
       │         SSE events ↓
       │         meta  → { conversation_id, llm, route }
       │         token → { content }   (many times)
       │         done  → { conversation_id, content, route, rag }
       │         error → { code, message }
       ├─ 6. save assistant message + touch conversation + commit
       └─ 7. every 4 messages → ARQ summarize_conversation
```

### 4. Chat complete (non-SSE)

Endpoint: `POST /api/v1/chat/complete`  
Same business steps, but `run_chat()` retrieves then returns one `ChatCompleteResponse` JSON.

### 5. Chat AI flow — `ai/chat.py`

```
use_rag? → Retriever → rag_context → LLM (stream or complete)
```

| Piece        | Code                 | Job                        |
| ------------ | -------------------- | -------------------------- |
| chat flow    | `ai/chat.py`         | `stream_chat` / `run_chat` |
| RAG retrieve | `ai/rag/retrieve.py` | Vector → keyword fallback  |
| pgvector     | `ai/rag/pgvector.py` | Cosine distance            |
| LLM          | `ai/llm/`            | Gemini / OpenAI / demo     |
| prompts      | `ai/prompts/chat.py` | System + RAG context       |

### 6. Background jobs (ARQ)

| Job                      | Trigger               | Does                                      |
| ------------------------ | --------------------- | ----------------------------------------- |
| `summarize_conversation` | Chat every 4 messages | LLM summary → save `Conversation.summary` |
| `process_document`       | After document create | Embed chunks → pgvector                   |

Worker command: `arq app.jobs.worker.WorkerSettings`

### 7. Health

`GET /api/v1/health` (no JWT) — Postgres + Redis + LLM provider label. Fail soft per check.

### 8. One-turn checklist (interview / demo)

1. Register / login → JWT  
2. (Optional) upload document → chunks + optional embeddings  
3. Send chat → SSE tokens appear in UI  
4. Message rows in Postgres (Adminer)  
5. After ~4 messages, worker may write a conversation summary  

## Docker services

| Service   | Role                                      | Port |
| --------- | ----------------------------------------- | ---- |
| `api`     | uvicorn FastAPI (`--reload`)              | 8000 |
| `worker`  | ARQ (`arq app.jobs.worker.WorkerSettings`)| —    |
| `postgres`| pgvector/pg16                             | 5432 |
| `redis`   | rate limit + ARQ broker                   | 6379 |
| `adminer` | DB UI                                     | 8080 |

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

| Service       | URL                                 |
| ------------- | ----------------------------------- |
| API / OpenAPI | http://localhost:8000/docs          |
| Health        | http://localhost:8000/api/v1/health |
| Adminer       | http://localhost:8080               |

Leave `GEMINI_API_KEY` empty for demo streaming (no real LLM).

Then start the UI from `../frontend` with `npm run dev` → http://localhost:3000

Register or log in from the UI. There is no demo auto-login.

## Tests

This backend runs in Docker. You do **not** need a local `pip` / `pytest` on Windows.

```powershell
docker compose up -d --build
docker compose run --rm api pytest
```

Optional local Python (only if you want host-side pytest): install [Python 3.12+](https://www.python.org/downloads/) with **Add python.exe to PATH**, then:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

## Comment style

Logic comments use section blocks under `app/` (see `.cursor/rules/python-comments.mdc`):

```python
# ---------------------------------------------------------------------------
# Title — short why
# ---------------------------------------------------------------------------
```
