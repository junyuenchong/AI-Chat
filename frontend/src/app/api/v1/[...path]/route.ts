/**
 * Next.js API proxy — forwards /api/v1/* to FastAPI.
 *
 * Request path:
 *   Browser fetch("/api/v1/...")
 *     → app/api/v1/[...path]/route.ts  (this file)
 *     → FastAPI http://localhost:8000/api/v1/...
 */

import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);

// ────────────────────────────────────────────────────────
// proxy
// Path: app/api/v1/[...path]/route.ts
// Use: forward method, body, and Authorization header to FastAPI.
// ────────────────────────────────────────────────────────
async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const search = new URL(req.url).search;
  const target = `${BACKEND}/api/v1/${path.join("/")}${search}`;
  const isStream = path.join("/") === "chat/stream";

  // Step 1 — copy auth and content-type headers to the backend request.
  const headers = new Headers();
  const auth = req.headers.get("authorization");
  const contentType = req.headers.get("content-type");
  if (auth) headers.set("authorization", auth);
  if (contentType) headers.set("content-type", contentType);

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  // Step 2 — forward request body for POST/PUT/PATCH/DELETE.
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body;
    (init as RequestInit & { duplex: "half" }).duplex = "half";
  }

  let res: Response;
  try {
    res = await fetch(target, init);
  } catch (error) {
    // Step 3 — backend down → return 503 JSON the UI can display.
    const detail =
      error instanceof Error ? error.message : "Could not reach the FastAPI backend.";
    return new Response(
      JSON.stringify({
        error: {
          code: "BACKEND_UNAVAILABLE",
          message:
            "API server is unreachable. Start the backend (docker compose up) and try again.",
          fields: [{ field: "detail", message: detail }],
        },
      }),
      {
        status: 503,
        headers: { "content-type": "application/json" },
      },
    );
  }

  // Step 4 — pass through response headers (disable caching for SSE).
  const out = new Headers();
  const pass = ["content-type", "cache-control", "x-accel-buffering"];
  for (const key of pass) {
    const value = res.headers.get(key);
    if (value) out.set(key, value);
  }
  out.set("cache-control", "no-cache, no-transform");

  if (isStream) {
    out.set("content-type", "text/event-stream; charset=utf-8");
    out.set("x-accel-buffering", "no");
    out.set("connection", "keep-alive");
  }

  // Step 5 — non-stream responses pass through directly.
  if (!isStream || !res.body) {
    return new Response(res.body, { status: res.status, headers: out });
  }

  // Step 6 — stream SSE chunks without buffering the full body.
  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body!.getReader();
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          if (value) controller.enqueue(value);
        }
      } finally {
        controller.close();
      }
    },
  });
  return new Response(stream, { status: res.status, headers: out });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  return proxy(req, (await ctx.params).path);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  return proxy(req, (await ctx.params).path);
}

export async function PUT(req: NextRequest, ctx: Ctx) {
  return proxy(req, (await ctx.params).path);
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  return proxy(req, (await ctx.params).path);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  return proxy(req, (await ctx.params).path);
}
