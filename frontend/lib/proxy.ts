import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Forwards a JSON body to a backend endpoint and relays the response
 * (and status code) back as-is. Used by every /api/* route below except
 * /api/begin, which forwards multipart form data instead of JSON.
 */
export async function proxyJson(backendPath: string, body: unknown) {
  const res = await fetch(`${BACKEND_URL}${backendPath}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
