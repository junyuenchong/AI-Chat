# c

Full-stack portfolio chat: **Next.js UI** + **FastAPI** + **LangChain / RAG** (no LangGraph, no n8n).

## What each piece does


| Piece         | Role                                                            |
| ------------- | --------------------------------------------------------------- |
| **LangChain** | AI components — prompts, LLM, embeddings, chunking              |
| **RAG**       | Retriever finds Knowledge chunks, then LLM answers with context |
| **FastAPI**   | HTTP API, JWT auth, SSE streaming                               |
| **Next.js**   | Chat UI (auth, conversations, knowledge, stream)                |
| **Postgres**  | Users, conversations, messages, documents + pgvector            |
| **Redis/ARQ** | Rate limits + background summarize / embed jobs                 |


Gemini or OpenAI powers the same RAG chat flow. Empty API keys → demo streaming.

## Domain glossary

**Conversation** = user's chat history.  
**Knowledge** = information the AI can retrieve from.


| Term             | Meaning                            |
| ---------------- | ---------------------------------- |
| **Conversation** | Chat history (one thread)          |
| **Message**      | Individual chat turn               |
| **Chat**         | AI interaction (stream / complete) |
| **Knowledge**    | AI knowledge base                  |
| **Document**     | Uploaded / source file             |
| **Chunk**        | Split document content             |
| **Retriever**    | Finds relevant knowledge           |
| **RAG**          | Retrieved knowledge + LLM          |


### Example

User asks: *"What is our company's annual leave policy?"*

```
Conversation                          Knowledge
└── Message                           └── company_handbook.pdf  (Document)
      └── User: What is our company's       ├── Chunk 1
          annual leave policy?              ├── Chunk 2  ← relevant
                                            └── Chunk 3
```

```
Conversation → Chat API → Retriever
    → Knowledge / Vector Store → RAG → LLM → Assistant Message
```

```
Knowledge → Document → Chunk
Chat → Conversation → Message
RAG = Retriever(Chunks) + LLM
```

Full backend detail: [backend/README.md](backend/README.md).

## Folders


| Folder        | Role                                   |
| ------------- | -------------------------------------- |
| **backend/**  | FastAPI + AI + Postgres/Redis — Docker |
| **frontend/** | Next.js chat UI — run locally with npm |


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


| Service | URL                                                                        |
| ------- | -------------------------------------------------------------------------- |
| Chat UI | [http://localhost:3000](http://localhost:3000)                             |
| OpenAPI | [http://localhost:8000/docs](http://localhost:8000/docs)                   |
| Health  | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) |
| Adminer | [http://localhost:8080](http://localhost:8080)                             |


Register or log in from the chat UI. There is no demo auto-login.

Leave `GEMINI_API_KEY` empty for demo (no real LLM) streaming.

## Backend layout

```
backend/app/
  main.py
  api/v1/      # HTTP: router + dto + mapping
  core/        # config, security, errors, JWT deps
  models/      # SQLAlchemy tables
  db/          # session + SQL access
  services/    # business logic
  ai/          # llm, prompts, rag, chat flow
  clients/     # Redis, ARQ
  jobs/        # background worker + tasks
```

Flow: **API → Services → db/Models + AI (optional RAG → LLM)**.


| Doc                                      | Contents                               |
| ---------------------------------------- | -------------------------------------- |
| [backend/README.md](backend/README.md)   | Architecture, workflows, Docker, tests |
| [frontend/README.md](frontend/README.md) | UI layout, API proxy, SSE notes        |


