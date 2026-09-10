import type {
  BeginInterviewResponse,
  NextQuestionResponse,
  SubmitAnswerResponse,
  ReportResponse,
  ApiErrorBody,
} from "./types";

/**
 * All calls below hit our OWN Next.js API routes (app/api/*), never the
 * FastAPI backend directly. The proxy routes hold BACKEND_URL server-side,
 * so it's never shipped to the browser bundle.
 */

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiErrorBody;
    return body.detail || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function beginInterview(
  resumeFile: File,
  jdText: string
): Promise<BeginInterviewResponse> {
  const form = new FormData();
  form.append("file", resumeFile);
  form.append("jd_text", jdText);

  const res = await fetch("/api/begin", { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function getNextQuestion(
  sessionId: string
): Promise<NextQuestionResponse> {
  const res = await fetch("/api/next-question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function submitAnswer(
  sessionId: string,
  answer: string
): Promise<SubmitAnswerResponse> {
  const res = await fetch("/api/submit-answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answer }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function getReport(sessionId: string): Promise<ReportResponse> {
  const res = await fetch("/api/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}
