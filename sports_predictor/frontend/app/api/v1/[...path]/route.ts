import { NextRequest, NextResponse } from "next/server";

const BACKEND = "https://pi-ebook-store-production.up.railway.app";

async function proxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = (await params).path.join("/");
  const { search } = new URL(req.url);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const auth = req.headers.get("authorization");
  if (auth) headers["Authorization"] = auth;

  const body =
    req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

  try {
    const upstream = await fetch(`${BACKEND}/api/v1/${path}${search}`, {
      method: req.method,
      headers,
      body,
    });

    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
