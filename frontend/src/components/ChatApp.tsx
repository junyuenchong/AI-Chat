"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import {
  API_BASE,
  apiJson,
  authHeaders,
  formatApiError,
  readError,
  readSse,
  streamUrl,
} from "@/lib/api";
import type { Conversation, ConversationDetail, DocumentOut, Health } from "@/lib/types";

const TOKEN_KEY = "ai_chat_token";

type Bubble = { role: "user" | "assistant"; content: string };
type AuthMode = "login" | "register";

export default function ChatApp() {
  const [token, setToken] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [title, setTitle] = useState("New conversation");
  const [bubbles, setBubbles] = useState<Bubble[]>([
    {
      role: "assistant",
      content:
        "Stack is up. Try: What is the difference between LangChain and RAG?",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState("notes.md");
  const [docContent, setDocContent] = useState("");
  const messagesRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  const loadHealth = useCallback(async () => {
    try {
      const data = await apiJson<Health>("/api/v1/health");
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  const loadConversations = useCallback(async (jwt: string) => {
    try {
      const rows = await apiJson<Conversation[]>("/api/v1/conversations", { token: jwt });
      setConversations(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load conversations.");
    }
  }, []);

  const loadDocuments = useCallback(async (jwt: string) => {
    try {
      const rows = await apiJson<DocumentOut[]>("/api/v1/documents", { token: jwt });
      setDocuments(rows);
    } catch {
      setDocuments([]);
    }
  }, []);

  const applySession = useCallback(
    async (jwt: string) => {
      sessionStorage.setItem(TOKEN_KEY, jwt);
      setToken(jwt);
      setError(null);
      await loadConversations(jwt);
      await loadDocuments(jwt);
    },
    [loadConversations, loadDocuments],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await loadHealth();
      const saved = sessionStorage.getItem(TOKEN_KEY);
      if (!saved) {
        if (!cancelled) setAuthReady(true);
        return;
      }
      try {
        await apiJson("/api/v1/auth/me", { token: saved });
        if (cancelled) return;
        await applySession(saved);
      } catch {
        sessionStorage.removeItem(TOKEN_KEY);
        if (!cancelled) setToken(null);
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [applySession, loadHealth]);

  useEffect(() => {
    scrollToBottom();
  }, [bubbles]);

  async function onAuth(event: FormEvent) {
    event.preventDefault();
    if (authBusy) return;
    setAuthBusy(true);
    setError(null);
    try {
      const path = authMode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
      const body =
        authMode === "register"
          ? { email, password, name }
          : { email, password };
      const data = await apiJson<{ access_token: string }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      await applySession(data.access_token);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setAuthBusy(false);
    }
  }

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setConversations([]);
    setDocuments([]);
    setConversationId(null);
    setTitle("New conversation");
    setBubbles([
      {
        role: "assistant",
        content: "Sign in to start chatting.",
      },
    ]);
    setError(null);
  }

  async function openConversation(id: string) {
    if (!token) return;
    setError(null);
    try {
      const data = await apiJson<ConversationDetail>(`/api/v1/conversations/${id}`, {
        token,
      });
      setConversationId(id);
      setTitle(data.title);
      setBubbles(data.messages.map((msg) => ({ role: msg.role as Bubble["role"], content: msg.content })));
      await loadConversations(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not open conversation.");
    }
  }

  function newChat() {
    setConversationId(null);
    setTitle("New conversation");
    setBubbles([
      {
        role: "assistant",
        content:
          "New chat. LangChain supplies LLM/RAG components. Chat flow retrieves knowledge then calls the LLM.",
      },
    ]);
    if (token) void loadConversations(token);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (streaming || !token) return;
    const message = input.trim();
    if (!message) return;
    setInput("");
    setError(null);
    setBubbles((prev) => [...prev, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const body: { message: string; use_rag: boolean; conversation_id?: string } = {
        message,
        use_rag: true,
      };
      if (conversationId) body.conversation_id = conversationId;
      const res = await fetch(streamUrl("/api/v1/chat/stream"), {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await readError(res, "Chat request failed.");
        setBubbles((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: "assistant", content: text };
          return next;
        });
        return;
      }
      await readSse(res, (eventName, data) => {
        if (eventName === "meta" && typeof data.conversation_id === "string") {
          setConversationId(data.conversation_id);
        }
        const tokenText =
          (eventName === "token" || eventName === "message") && typeof data.content === "string"
            ? data.content
            : null;
        if (tokenText) {
          setBubbles((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { role: "assistant", content: (last?.content || "") + tokenText };
            return next;
          });
        }
        if (eventName === "done") {
          if (typeof data.conversation_id === "string") {
            setConversationId(data.conversation_id);
            setTitle(message.slice(0, 80));
          }
          if (typeof data.content === "string" && data.content) {
            setBubbles((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last?.role !== "assistant") return next;
              next[next.length - 1] = {
                role: "assistant",
                content: last.content || (data.content as string),
              };
              return next;
            });
          }
        }
        if (eventName === "error") {
          setBubbles((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: formatApiError(data, "Stream error"),
            };
            return next;
          });
        }
      });
      await loadConversations(token);
    } catch (err) {
      setBubbles((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: err instanceof Error ? err.message : String(err),
        };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  async function uploadDocument(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await apiJson("/api/v1/documents", {
        method: "POST",
        token,
        body: JSON.stringify({ filename, content: docContent }),
      });
      setDocContent("");
      await loadDocuments(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload document.");
    }
  }

  if (!authReady) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1>AI Chat</h1>
          <p>Loading…</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1>{authMode === "login" ? "Sign in" : "Create account"}</h1>
          <p>LangChain · RAG. Register or log in to chat.</p>
          <form onSubmit={onAuth}>
            {authMode === "register" ? (
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Name"
                autoComplete="name"
                required
              />
            ) : null}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              autoComplete="email"
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              autoComplete={authMode === "register" ? "new-password" : "current-password"}
              minLength={authMode === "register" ? 6 : 1}
              required
            />
            <button type="submit" disabled={authBusy}>
              {authBusy ? "Please wait…" : authMode === "login" ? "Sign in" : "Register"}
            </button>
          </form>
          {error ? <div className="hint error">{error}</div> : null}
          <div className="auth-switch">
            {authMode === "login" ? (
              <>
                No account?{" "}
                <button type="button" onClick={() => { setAuthMode("register"); setError(null); }}>
                  Register
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button type="button" onClick={() => { setAuthMode("login"); setError(null); }}>
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <aside>
        <div className="brand">
          <h1>AI Chat</h1>
          <p>
            LangChain = AI Components
            <br />
            RAG = Retriever + Knowledge + LLM
          </p>
          <div className="status">
            <span className={`pill ${health?.llm && health.llm !== "demo" ? "on" : "off"}`}>{health?.llm || "llm"}</span>
            <span className={`pill ${health?.postgres ? "on" : "off"}`}>postgres</span>
            <span className={`pill ${health?.redis ? "on" : "off"}`}>redis</span>
          </div>
        </div>
        <div className="actions">
          <button type="button" onClick={newChat}>
            New chat
          </button>
          <button type="button" className="ghost" onClick={() => loadConversations(token)}>
            Refresh
          </button>
          <button type="button" className="ghost" onClick={logout}>
            Log out
          </button>
        </div>
        <div className="list">
          {conversations.map((row) => (
            <button
              key={row.id}
              type="button"
              className={`item ${row.id === conversationId ? "active" : ""}`}
              onClick={() => openConversation(row.id)}
            >
              <div>{row.title}</div>
              <small>{row.summary ? row.summary.slice(0, 80) : ""}</small>
            </button>
          ))}
        </div>
        <form className="docs" onSubmit={uploadDocument}>
          <strong>RAG documents</strong>
          {documents.map((doc) => (
            <small key={doc.id}>{doc.filename}</small>
          ))}
          <input value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="filename.md" />
          <textarea
            value={docContent}
            onChange={(e) => setDocContent(e.target.value)}
            placeholder="Paste knowledge for RAG..."
            rows={3}
          />
          <button type="submit" className="ghost">
            Upload
          </button>
        </form>
      </aside>
      <main>
        <header className="bar">
          <div>
            <strong>{title}</strong>
            <br />
            <span>Next.js · FastAPI · LangChain · RAG · SSE</span>
          </div>
          <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
            OpenAPI
          </a>
        </header>
        <div className="messages" ref={messagesRef}>
          {bubbles.map((bubble, index) => (
            <div key={`${bubble.role}-${index}`} className={`bubble ${bubble.role}`}>
              {bubble.content || (streaming && index === bubbles.length - 1 && bubble.role === "assistant" ? (
                <span className="typing">Thinking…</span>
              ) : null)}
            </div>
          ))}
        </div>
        {error ? <div className="hint error">{error}</div> : null}
        <div className="hint">Ask about LangChain vs RAG. Streaming uses POST /api/v1/chat/stream.</div>
        <form className="composer" onSubmit={onSubmit}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={streaming ? "Waiting for reply..." : "Send a message..."}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <button type="submit" disabled={streaming || !input.trim()}>
            {streaming ? "Sending..." : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}
