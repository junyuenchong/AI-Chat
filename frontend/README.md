# Next.js Frontend

Chat UI for the FastAPI backend — feature-oriented structure for SaaS growth.

Handles **authentication**, **conversation sidebar**, **streaming chat**, and **knowledge document upload**.

Runs locally with **npm** (no Docker required for the frontend).

---

## Architecture

```
app/           → routing only (Next.js App Router)
features/      → business functionality (auth, chat, conversations, knowledge)
components/ui/ → reusable UI primitives
lib/           → shared HTTP client and SSE reader
```

| Layer | Role |
| --- | --- |
| `app/` | Route groups: `(auth)` for login/register, `(dashboard)` for chat and knowledge |
| `features/` | Each feature owns `components/`, `api.ts`, `hooks.ts`, `types.ts` |
| `components/ui/` | Shared Button, Input, Loading (Tailwind styled) |
| `lib/` | Generic `apiJson`, `readSse`, `cn` utility; proxy returns 503 when API is down |

### Features

| Feature | Folder | Endpoints |
| --- | --- | --- |
| Auth | `features/auth/` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Chat | `features/chat/` | `POST /chat/stream` |
| Conversations | `features/conversations/` | `GET /conversations`, `GET /conversations/{id}` |
| Knowledge | `features/knowledge/` | `GET /documents`, `POST /documents` |
| Health | `features/health/` | `GET /health` |

---

## Project structure

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── chat/page.tsx
│   │   ├── knowledge/page.tsx
│   │   └── DashboardLayout.tsx
│   ├── api/v1/[...path]/route.ts    # Proxy to FastAPI
│   ├── layout.tsx
│   └── providers.tsx
├── features/
│   ├── auth/
│   ├── chat/
│   ├── conversations/
│   ├── knowledge/
│   └── health/
├── components/ui/
└── lib/
    ├── api/client.ts
    ├── sse/reader.ts
    └── types/common.ts
```

---

## Routes

| Path | Use |
| --- | --- |
| `/login` | Sign in |
| `/register` | Create account |
| `/chat` | Main chat UI with sidebar threads |
| `/knowledge` | Upload and list RAG documents |

---

## Quick start

```powershell
# Terminal 1 — backend
cd ..\backend
Copy-Item .env.example .env
docker compose up --build

# Terminal 2 — frontend
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000** → redirects to `/chat` (login required).

The Next.js proxy at `src/app/api/v1/[...path]/route.ts` forwards cookies to FastAPI. If the backend is not running, API calls return **503** with a clear JSON error (not a generic 500).

---

## Chat streaming (SSE)

The chat UI consumes Server-Sent Events from `POST /chat/stream`:

| Event | UI behavior |
| --- | --- |
| `meta` | Updates `conversation_id` in sidebar |
| `token` | Appends text to the assistant bubble |
| `done` | Finalizes message and refreshes conversation list |
| `error` | Shows LLM failure message (`code: LLM_ERROR`) — not mixed into tokens |

Parsed in `features/chat/hooks.ts` via `lib/sse/reader.ts`.

---

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI base URL for the Next.js proxy |

---

## Styling

The UI uses **Tailwind CSS v4** with a custom dark theme defined in `src/app/globals.css` (`@theme` tokens: `bg-panel`, `text-muted`, `border-line`, etc.). Component styles live as utility classes — no separate stylesheet per feature.

---

Each hook and component function includes block comments:

```tsx
// ────────────────────────────────────────────────────────
// useChat
// Feature: chat
// Endpoint: POST /chat/stream
// Use: manage message bubbles and streaming state.
// ────────────────────────────────────────────────────────
```

---

## Related docs

| Document | Purpose |
| --- | --- |
| [../README.md](../README.md) | Project overview |
| [../backend/README.md](../backend/README.md) | API routes and Docker |
