# AI Chat

Full-stack portfolio chat: **Next.js** + **FastAPI** + **LangChain** (LLM/embeddings) + **RAG** (retrieve + answer).

No LangGraph. No n8n.

## LangChain vs RAG (read this first)

| Layer | What it is | Uses LangChain? | Where |
| --- | --- | --- | --- |
| **LangChain** | AI model layer — prompts, chat LLM, embeddings, summarize | **Yes** | `backend/app/ai/llm`, `prompts`, `rag/embeddings.py` |
| **RAG** | Retrieve Knowledge chunks → pass to LLM | **Partly** | `ai/rag/` (embeddings = LC; chunk/search = custom) |
| **App** | HTTP, auth, DB, SSE, jobs | **No** | `api/`, `services/`, `db/`, `jobs/` |

```
Knowledge ingest:  Document → split (Python) → embed (LangChain) → pgvector (Postgres)
Chat:              optional Retriever (SQL) → prompt + LLM (LangChain) → SSE
```

Gemini or OpenAI when `GEMINI_API_KEY` / `OPENAI_API_KEY` is set. Empty keys → **demo** streaming (real HTTP, DB, SSE — mock LLM text).

## Domain glossary

**Conversation** = chat history. **Knowledge** = what the AI can retrieve.

| Term | Meaning |
| --- | --- |
| **Conversation** | One chat thread (sidebar item) |
| **Message** | One user or assistant turn |
| **Chat** | AI call — stream or complete |
| **Knowledge** | User's RAG document store |
| **Document** | Uploaded source file (text) |
| **Chunk** | Split piece of a document |
| **Retriever** | Finds relevant chunks for a query |
| **RAG** | Retriever + LLM (context-aware answer) |

**Example:** *"What is our annual leave policy?"* → Retriever picks a chunk from `company_handbook.pdf` → LangChain LLM answers using that context → saved as an assistant **Message** in the **Conversation**.

## Folders

| Folder | Role |
| --- | --- |
| [backend/](backend/) | FastAPI + AI + Postgres/Redis — Docker |
| [frontend/](frontend/) | Next.js chat UI — npm locally |

## Quick start

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build

cd ..\frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

| Service | URL |
| --- | --- |
| Chat UI | http://localhost:3000 |
| OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| Adminer | http://localhost:8080 |

Register or log in from the UI. No demo auto-login.

## Docs

| File | Contents |
| --- | --- |
| [backend/README.md](backend/README.md) | Layout, workflows, Docker, tests |
| [frontend/README.md](frontend/README.md) | UI, JSON proxy, SSE wiring |
