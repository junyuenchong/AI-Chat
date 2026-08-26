import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const search = new URL(req.url).search;
  const target = `${BACKEND}/api/v1/${path.join("/")}${search}`;
  const isStream = path.join("/") === "chat/stream";
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
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body;
    // Node fetch needs duplex when forwarding a streamed body.
    (init as RequestInit & { duplex: "half" }).duplex = "half";
  }

  const res = await fetch(target, init);
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

  if (!isStream || !res.body) {
    return new Response(res.body, { status: res.status, headers: out });
  }

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
