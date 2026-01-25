import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();
  const baseUrl = process.env.K9_API_BASE_URL || "http://localhost:8000";
  const normalizedBaseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;

  const upstream = await fetch(`${normalizedBaseUrl}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}

