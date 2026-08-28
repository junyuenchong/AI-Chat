# AI Chat

Full-stack chat application with **RAG** (retrieval-augmented generation).

| Layer | Technology |
| --- | --- |
| Frontend | Next.js — chat UI, auth, knowledge upload |
| Backend | FastAPI — REST API, SSE streaming, background jobs |
| AI | LangChain — LLM and embeddings (Gemini or OpenAI) |
| Data | PostgreSQL + pgvector, Redis |

**Not used:** LangGraph, n8n.

---

## What this app does

Users can **register**, **chat** with an AI assistant (streaming or JSON), manage **conversation history**, and upload **knowledge documents** that the AI can search when answering questions.

| Term | Meaning |
| --- | --- |
| **Conversation** | One chat thread (shown in the sidebar) |
| **Message** | A single user or assistant turn inside a conversation |
| **Knowledge** | Documents uploaded for RAG search |
| **Document** | One uploaded text file |
| **Chunk** | A small piece of a document used for search |
| **RAG** | Search relevant chunks → pass them to the LLM → answer with context |

**Example:** User asks *"What is our leave policy?"* → retriever finds a matching chunk → LLM answers using that text → reply is saved as a message in the conversation.

---

## Repository layout

```
FastApi/
├── backend/          FastAPI API, AI, database, Docker Compose
├── frontend/         Next.js chat UI (run with npm)
└── docs/             Testing, security, and presentation notes
```

| README | Contents |
| --- | --- |
| [backend/README.md](backend/README.md) | Architecture, API routes, Docker, tests |
| [frontend/README.md](frontend/README.md) | UI setup, API proxy, SSE wiring |

---

## Quick start

### 1. Backend (Docker)

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build
```

### 2. Frontend (local)

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

### 3. Open the app

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |
| Database UI (Adminer) | http://localhost:8080 |

Register or log in from the UI. There is no demo auto-login.

### LLM modes

| Configuration | Behavior |
| --- | --- |
| `GEMINI_API_KEY` or `OPENAI_API_KEY` set | Real LLM responses via LangChain |
| Keys empty | **Demo mode** — real HTTP, database, and SSE; mock LLM text |

---

## API overview

All routes are under `/api/v1`.

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/health` | Service status and dependency flags |
| `POST` | `/auth/register` | Create account and start a session |
| `POST` | `/auth/login` | Log in and start a session |
| `POST` | `/auth/logout` | End session and clear cookie |
| `GET` | `/auth/me` | Load current user profile |
| `GET` | `/conversations` | List chat threads (sidebar) |
| `GET` | `/conversations/{id}` | Load one thread with messages |
| `DELETE` | `/conversations/{id}` | Delete a thread |
| `POST` | `/chat/stream` | Stream AI reply via SSE |
| `POST` | `/chat/complete` | Return full AI reply as JSON |
| `GET` | `/documents` | List uploaded knowledge documents |
| `POST` | `/documents` | Upload a document for RAG |
| `DELETE` | `/documents/{id}` | Delete a document |

---

## Architecture (high level)

```
Browser (Next.js)
    ↓  JSON + SSE (cookie session or Bearer JWT)
FastAPI routers  →  application services  →  domain ports
                              ↓
                    infrastructure (Postgres, Redis, LangChain, ARQ worker)
```

- **Routers** handle HTTP only.
- **Application** layer contains business logic (`service.py`, `mapper.py`, `helpers.py`).
- **Domain** defines entities and ports (`LLMPort`, `RetrieverPort`).
- **Infrastructure** implements database, AI, cache, and background jobs.

Details: [backend/README.md](backend/README.md).

---

## Further reading

| Document | Purpose |
| --- | --- |
| [docs/TESTING.md](docs/TESTING.md) | How to run unit, integration, and e2e tests |
| [docs/SECURITY.md](docs/SECURITY.md) | Sessions, rate limits, auth |
| [docs/PRESENTATION.md](docs/PRESENTATION.md) | Demo walkthrough script |
