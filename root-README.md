# AI Interview Prep Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)
![Next.js](https://img.shields.io/badge/Next.js-App%20Router-black)
![LLM](https://img.shields.io/badge/LLM-Groq-orange)
![Status](https://img.shields.io/badge/status-active--development-yellow)

An agentic AI mock-interview coach. Upload a resume and a job description — a multi-agent LangGraph pipeline finds the gaps between them, runs an adaptive mock interview targeting those gaps, and produces a reasoning-based feedback report, not just a score.

🔗 **[Live demo](https://ai-interview-prep-agent-eight.vercel.app)** · **[API docs](http://13.204.132.141:8000/docs)**

---

## What it does

Most "AI interview prep" tools ask generic questions from a job title and grade answers with a single opaque score. A real interviewer reads your resume against the job description first, decides what to probe, and adapts based on your answers — this project does the same:

1. **Parses** your resume and the job description into structured data.
2. Runs a **gap analysis** — where you're strong, where you're weak, relative to *this specific job*.
3. **Generates tailored questions** that prioritize your actual weak spots and your real projects.
4. Conducts a **turn-based interview**, evaluating each answer with reasoning as you go — including follow-ups when an answer is incomplete.
5. Produces a **report**: overall score, category breakdown, which job-requirement gaps you actually closed in the interview, and what to work on next.

Sessions persist server-side, so refreshing mid-interview resyncs instead of losing progress.

## Architecture

```
Resume (PDF/DOCX) ──┐
                     ├──►  Analyzer Agent  ──►  Gap Analysis
Job Description ─────┘            │
                                   ▼
                       Question Generator Agent
                                   │
                                   ▼
                       Interviewer Agent  (conversational loop)
                            │           ▲
                            ▼           │ follow-up if needed
                       User's Answer ───┘
                                   │
                                   ▼
                       Critic / Evaluator Agent  (score + reasoning)
                                   │
                                   ▼
                       Report Generator Agent  ──►  "How it went" report
```

Each stage is a distinct agent with a narrow responsibility — not one prompt wearing several hats. See [`backend/README.md`](./backend/README.md#4-design-decisions) for the full reasoning behind the multi-agent design, the LangGraph state shape, and the session-locking approach.

## Project structure

```
.
├── backend/    FastAPI + LangGraph agent pipeline  → see backend/README.md
├── frontend/   Next.js UI                          → see frontend/README.md
└── .github/workflows/   CI/CD: build → Docker Hub → deploy to EC2
```

- **[`backend/README.md`](./backend/README.md)** — architecture deep-dive, design decisions, full API reference, setup, and testing.
- **[`frontend/README.md`](./frontend/README.md)** — UI structure, design notes, and setup.

## Tech stack

| Layer | Tech |
|---|---|
| Agent orchestration | LangGraph (StateGraph, SQLite checkpointer) |
| LLM | Groq (Llama 3.3 70B) |
| Backend | FastAPI, Python 3.11+ |
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS |
| Deployment | Docker on AWS EC2 (backend), Vercel (frontend) |
| CI/CD | GitHub Actions — build → push to Docker Hub → deploy to EC2 |

## Quick start

Backend and frontend run independently — see their own READMEs for full setup:

```bash
# Backend
cd backend && cp .env.example .env   # add your GROQ_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend && cp .env.example .env.local   # BACKEND_URL=http://localhost:8000
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Roadmap

- [ ] HTTPS on the backend via a reverse proxy + managed certificate
- [ ] Voice-based answer input
- [ ] Expanded RAG knowledge base with role-specific question banks
- [ ] Support for more resume formats

---

Built by [Ali Raza](https://github.com/AliRaza3485)
