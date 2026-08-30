# AI Chat (Question 2)

Minimal **streaming LLM chat**: FastAPI SSE + Postgres session memory + LangChain + Next.js.

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.12 |
| AI | LangChain — Chat Model + Messages + `astream()` only |
| Data | PostgreSQL (conversation history) |
| Auth | JWT Bearer token (`sessionStorage` on the client) |

**Q2 core:** token streaming · chat history in Postgres · JWT auth · Clean Architecture · Docker · tests · inline code comments

**Not in scope:** RAG · vector DB · Redis · worker · LangGraph · agents · tools · cookie sessions

---

## Quick start

### Backend

```powershell
cd backend
Copy-Item .env.example .env
docker compose down -v --remove-orphans   # optional — fresh DB
docker compose up --build
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

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Adminer | http://localhost:8080 |

**Demo login:** `demo@example.com` / `demo123` (created by seeds)

**New email?** Use **Register** first — accounts are not created at login.

Leave `GEMINI_API_KEY` and `OPENAI_API_KEY` empty for **demo mode** (real HTTP, DB, SSE; mock LLM text).

---

## Architecture

```
Browser (Next.js)
   ↓  Authorization: Bearer <JWT>
/api/v1/[...path]/route.ts   ← same-origin proxy (dev)
   ↓
FastAPI (Chat Service)
   ↓
┌──────────────┬─────────────────────┐
│  PostgreSQL  │      LangChain      │
│  (history)   │  Chat Model         │
│              │  Messages           │
│              │  astream()          │
└──────────────┴─────────────────────┘
   ↓
Gemini / OpenAI (or demo mode)
```

**Postgres** stores conversations and messages. **LangChain** only handles LLM calls — not persistence.

---

## Q2 chat flow

```
User message → save to Postgres → load history → build messages → llm.astream() → SSE tokens → save reply
```

### LangChain components (Q2 minimal)

| Component | Purpose | Code |
| --- | --- | --- |
| **Chat Model** | `ChatGoogleGenerativeAI` / `ChatOpenAI` | `infrastructure/ai/langchain/llm/factory.py` |
| **Messages** | `SystemMessage`, `HumanMessage`, `AIMessage` | `infrastructure/ai/langchain/llm/messages.py` |
| **Streaming** | `llm.astream(messages)` | `infrastructure/ai/langchain/llm/provider.py` |

Plain string system prompt (no `ChatPromptTemplate`). History comes from Postgres, not LangChain Memory.

```
infrastructure/ai/langchain/
├── llm/          factory, provider, messages
├── prompts/      SYSTEM_PROMPT string
├── chains/       ChatChain (history + stream)
├── callbacks/    stream_llm_tokens helper
└── adapters/     build_chat_engine()
```

---

## API overview

Base path: `/api/v1`. Swagger: http://localhost:8000/docs

| Method | Path | Use |
| --- | --- | --- |
| `GET` | `/health` | Postgres + LLM provider status |
| `POST` | `/auth/register` | Create account → JWT |
| `POST` | `/auth/login` | Log in → JWT |
| `POST` | `/auth/logout` | No-op (client clears JWT) |
| `GET` | `/auth/me` | Current user (Bearer token) |
| `GET` | `/conversations` | List threads |
| `GET` | `/conversations/{id}` | Load thread + messages |
| `DELETE` | `/conversations/{id}` | Delete thread |
| `POST` | `/chat/stream` | Stream reply (SSE) |
| `POST` | `/chat/complete` | Full reply (JSON) |

### SSE events (`/chat/stream`)

| Event | Payload |
| --- | --- |
| `meta` | `conversation_id`, `llm`, `route`, `components` |
| `token` | `{ "content": "..." }` |
| `done` | `conversation_id`, `content` |
| `error` | `{ "code", "message" }` |

---

## Configuration

| Setting | Behavior |
| --- | --- |
| `GEMINI_API_KEY` | Real LLM via LangChain (Gemini) |
| `OPENAI_API_KEY` | Real LLM when Gemini key is empty |
| Both empty | Demo mode — mock LLM text |
| `GEMINI_MODEL` | Primary model (default `gemini-3.6-flash`) |
| `GEMINI_FALLBACK_MODEL` | Secondary model on failure (optional) |
| `LLM_RETRY_*` | Retry transient API errors |
| `JWT_SECRET_KEY` | Token signing (min 32 chars in production) |

Full list: [backend/.env.example](backend/.env.example)

---

## Code comments

Source files use a consistent comment style for interview walkthroughs:

- **Module docstring** — request path (which file calls this file)
- **Boxed block comment** per function — `Path`, `Endpoint`, `Use`
- **Inline steps** — `# Step 1 — ...` inside methods

Template: `backend/app/application/auth/service.py`

---

## Testing

```powershell
cd backend
docker compose run --rm api pytest          # 51 tests — demo mode (no live API)

cd ../frontend
npm test                                    # 41 tests
```

Pytest clears LLM API keys automatically so backend tests never call external APIs.

Details: [docs/TESTING.md](docs/TESTING.md) · [docs/PRESENTATION.md](docs/PRESENTATION.md) · [docs/SECURITY.md](docs/SECURITY.md)

---

## Repository

```
FastApi/
├── backend/     API, LangChain, Postgres, Docker
├── frontend/    Next.js chat UI + SSE proxy
└── docs/        Testing, presentation, security
```

| Document | Contents |
| --- | --- |
| [backend/README.md](backend/README.md) | API, migrations, env, pytest, Ruff |
| [frontend/README.md](frontend/README.md) | Routes, SSE, Jest, Playwright |
| [docs/PRESENTATION.md](docs/PRESENTATION.md) | 15–20 min demo script |
