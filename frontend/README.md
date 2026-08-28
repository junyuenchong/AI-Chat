# Next.js frontend

Chat UI for the FastAPI backend. **No Docker** — run with npm.

## Stack (UI labels)

| Pill / copy | Meaning |
| --- | --- |
| **LangChain** | Backend uses LC for LLM + embeddings (not chunking or SQL search) |
| **RAG** | Retriever finds Knowledge chunks, then LLM answers |
| **SSE** | `POST /api/v1/chat/stream` token stream |

**Conversation** = chat history sidebar. **Knowledge** = uploaded documents for RAG.

## Features

| Area | API |
| --- | --- |
| Auth | `POST /api/v1/auth/register\|login` · JWT in localStorage |
| Conversations | `GET /api/v1/conversations` |
| Chat | `POST /api/v1/chat/stream` (SSE) |
| Knowledge | `POST /api/v1/documents` |
| Health | `GET /api/v1/health` |

## Layout

```
src/
  app/
    page.tsx
    api/v1/[...path]/route.ts   # JSON proxy → FastAPI
  components/ChatApp.tsx        # main UI
  lib/api.ts                    # fetch + SSE reader
  lib/types.ts
```

## API wiring

| Type | Helper | Why |
| --- | --- | --- |
| JSON | `apiUrl()` | Browser → Next `/api/v1` proxy (no CORS) |
| SSE | `streamUrl()` | Browser → FastAPI direct (proxy buffers streams) |

Chat uses `fetch` + readable stream (POST + Bearer). Not `EventSource` (GET-only).

## Quick start

```powershell
# Terminal 1 — backend
cd ..\backend
Copy-Item .env.example .env
docker compose up --build

# Terminal 2 — frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 · register or log in (no demo auto-login).

## Env

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI base (JSON + SSE) |
