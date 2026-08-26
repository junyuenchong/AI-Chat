# Next.js frontend

Chat UI for the FastAPI backend. **No Docker** — run locally with npm.

Talks to the API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## What it does

| Feature            | How                                                              |
| ------------------ | ---------------------------------------------------------------- |
| Auth               | Register / login → JWT in local storage                          |
| Conversations      | Sidebar list + open thread (messages)                            |
| Chat               | `POST /api/v1/chat/stream` SSE tokens                            |
| Knowledge          | Upload document text → backend chunks + optional embed job       |
| Health             | Status pills (Postgres / Redis / LLM provider)                   |

Domain terms match the backend: **Conversation** = chat history, **Knowledge** = RAG documents.

## Layout

```
src/
  app/
    page.tsx                 # mounts ChatApp
    layout.tsx
    globals.css
    api/v1/[...path]/route.ts  # JSON proxy (same-origin; avoids CORS)
  components/
    ChatApp.tsx              # auth + chat + knowledge UI
  lib/
    api.ts                   # fetch helpers + SSE reader
    types.ts                 # Token, Conversation, Message, Health, …
```

## API wiring

| Call type | Path helper     | Target                                              |
| --------- | --------------- | --------------------------------------------------- |
| JSON      | `apiUrl()`      | Browser → Next `/api/v1/…` proxy → FastAPI          |
| SSE       | `streamUrl()`   | Browser → FastAPI directly (`NEXT_PUBLIC_API_URL`)  |

SSE hits FastAPI directly because the Next.js proxy can buffer `text/event-stream` chunks.

Chat uses `fetch` + streaming body (POST + Bearer JWT). Browser `EventSource` is GET-only, so it is not used.

## Quick start

Start the API first from `../backend`:

```powershell
cd ..\backend
Copy-Item .env.example .env
docker compose up --build
```

Then the UI:

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 and register or log in. There is no demo auto-login.

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Env

| Variable               | Default                   | Purpose                |
| ---------------------- | ------------------------- | ---------------------- |
| `NEXT_PUBLIC_API_URL`  | `http://localhost:8000`   | FastAPI base (SSE too) |

Backend OpenAPI: http://localhost:8000/docs  
Backend health: http://localhost:8000/api/v1/health
