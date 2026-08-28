# FastAPI backend

Production AI chat API (Docker). UI: `../frontend`.

**Stack:** FastAPI · LangChain (LLM + embeddings) · custom RAG · Postgres/pgvector · Redis/ARQ  
**Not used:** LangGraph · n8n

## LangChain vs custom code

| Concern | Technology | Module |
| --- | --- | --- |
| Chat LLM (stream / complete) | LangChain `ChatGoogleGenerativeAI` / `ChatOpenAI` | `ai/llm/` |
| Message objects | `langchain_core.messages` | `ai/llm/providers.py` |
| Embeddings | LangChain `GoogleGenerativeAIEmbeddings` / `OpenAIEmbeddings` | `ai/rag/embeddings.py` |
| Summarize job | LangChain LLM `ainvoke` | `ai/llm/providers.py` → `jobs/tasks.py` |
| Chunking | Plain Python `split_text()` | `ai/rag/service.py` |
| Vector search | SQLAlchemy + pgvector | `ai/rag/pgvector.py` |
| Retriever | SQL (vector → keyword → fallback) | `ai/rag/retrieve.py` |
| Chat orchestration | `retrieve → LLM` (no graph) | `ai/chat.py` |
| HTTP / auth / persist / SSE | FastAPI + SQLAlchemy | `api/`, `services/`, `db/` |

**Rule of thumb:** LangChain = **model calls**. RAG = **find chunks + call model**. Everything else = **FastAPI app code**.

## Layout

| Folder | Role |
| --- | --- |
| **api/** | HTTP routers, DTOs, mapping |
| **core/** | Config, security, JWT, errors |
| **models/** | SQLAlchemy tables |
| **db/** | Session + SQL access |
| **services/** | Business logic |
| **ai/** | LLM, prompts, RAG, chat flow |
| **clients/** | Redis, ARQ |
| **jobs/** | Background summarize + embed |

```
app/
  api/v1/          auth  chat  conversations  knowledge  health
  core/            config  security  dependencies  errors
  models/          user  conversation  message  document
  db/              session + repositories
  services/        auth  chat  conversation  knowledge
  ai/
    llm/           factory + providers (LangChain)
    prompts/       system + RAG + summarize text
    rag/           chunk  embed  pgvector  retrieve
    chat.py        optional RAG → LLM
  clients/         redis  queue
  jobs/            worker  tasks
```

## Domain glossary

| Term | Code / route |
| --- | --- |
| **Conversation** | `models/conversation.py` · `/api/v1/conversations` |
| **Message** | `models/message.py` |
| **Chat** | `services/chat.py` · `/api/v1/chat/stream\|complete` |
| **Knowledge** | `services/knowledge.py` · `/api/v1/documents` |
| **Document / Chunk** | `models/document.py` · `DocumentChunk` |
| **Retriever** | `ai/rag/retrieve.py` |
| **RAG** | `ai/rag/` + `ai/chat.py` |

## Chat flow (`ai/chat.py`)

```
use_rag?
  yes → Retriever → rag_context
  no  → skip
       ↓
LangChain LLM  →  SSE tokens or JSON complete
```

| Function | Endpoint | Job |
| --- | --- | --- |
| `stream_chat` | `POST /chat/stream` | retrieve → SSE meta/token/done |
| `run_chat` | `POST /chat/complete` | retrieve → one JSON reply |

## End-to-end workflows

### Auth

`POST /auth/register|login` → `services/auth` → `db/user` → JWT `TokenResponse`  
Protected routes: `get_current_user` (Bearer JWT).

### Knowledge ingest

```
POST /documents
  → save Document
  → split_text() → DocumentChunk rows
  → commit
  → ARQ process_document
       → LangChain embed
       → replace chunks + pgvector vectors
```

No API key: chunks saved; **keyword** retrieval works; embeddings stay `null`.

### Chat stream (main path)

`POST /chat/stream` · `EventSourceResponse` · UI uses `fetch` + stream (not `EventSource` — POST + JWT).

```
rate limit (Redis)
  → SessionLocal (SSE outlives request-scoped get_db)
  → get/create conversation
  → save user message + commit
  → ai/chat.stream_chat → SSE events:
       meta / token / done / error
  → save assistant message + commit
  → every 4 messages → ARQ summarize_conversation
```

### Background jobs (ARQ)

| Job | Trigger | Does |
| --- | --- | --- |
| `summarize_conversation` | Every 4 chat messages | LangChain summary → `Conversation.summary` |
| `process_document` | After document create | LangChain embed → pgvector |

Worker: `arq app.jobs.worker.WorkerSettings`

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

| Service | Port | Role |
| --- | --- | --- |
| `api` | 8000 | uvicorn `--reload` |
| `worker` | — | ARQ |
| `postgres` | 5432 | pgvector/pg16 |
| `redis` | 6379 | rate limit + queue |
| `adminer` | 8080 | DB UI |

| URL | |
| --- | --- |
| Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

Leave `GEMINI_API_KEY` empty for demo mode. Start UI: `cd ../frontend && npm run dev`.

## Tests

```powershell
docker compose up -d --build
docker compose run --rm api pytest
```

## Demo checklist

1. Register / login → JWT  
2. (Optional) upload document → chunks + embed job  
3. Chat → SSE tokens in UI  
4. Rows in Postgres (Adminer)  
5. ~4 messages → worker writes summary  

## Comments

Section blocks under `app/` — see `.cursor/rules/python-comments.mdc`.
