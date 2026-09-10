import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// Forwards the resume file + JD text straight through to the backend's
// single-entry-point endpoint. We stream the incoming FormData through
// untouched -- Next.js's fetch/FormData handles the multipart boundary
// for us, so there's no manual re-encoding to get wrong.
export async function POST(req: NextRequest) {
  const incomingForm = await req.formData();

  const res = await fetch(`${BACKEND_URL}/interview/begin`, {
    method: "POST",
    body: incomingForm,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
