# Frontend — AI Interview Prep Agent

Next.js (App Router) + TypeScript + Tailwind CSS. Talks to the FastAPI backend
in `../backend` through server-side proxy routes, so the backend's address is
never exposed to the browser.

## Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure the backend URL
cp .env.example .env.local
# edit .env.local — BACKEND_URL should point at your running backend
# (default: http://localhost:8000)

# 3. Run the dev server
npm run dev
```

Open `http://localhost:3000`. Make sure the backend (`../backend`, see the
root README) is running first — the landing page calls `/interview/begin` as
soon as you submit a resume + job description.

## Structure

```
app/
├── page.tsx                          Landing — resume upload + JD paste
├── interview/[sessionId]/page.tsx    Interview room — one question at a time
├── interview/[sessionId]/report/     Final report
└── api/                              Server-side proxy routes to the backend
components/                           UI building blocks (see below)
lib/
├── types.ts                          Mirrors backend Pydantic response models
├── api.ts                            Client-side fetch wrappers (call /api/*)
└── proxy.ts                          Server-side helper used by the /api routes
```

## Design notes

- **One accent color** (`amber`) is used only for progress and primary actions —
  everything else stays quiet on purpose, since this is a practice tool for an
  already-stressful moment (job interviews), not a dashboard.
- **One question at a time**, not a chat log — closer to how a real interview
  actually feels, and easier to focus on.
- **Session state lives in the URL** (`/interview/[sessionId]`), backed by the
  backend's SQLite session store — refreshing mid-interview resyncs instead of
  losing progress.
- **Server-side proxy routes** (`app/api/*`) keep `BACKEND_URL` out of the
  browser bundle, matching the pattern used in this author's other deployed
  projects (Next.js on Vercel + FastAPI on EC2).
