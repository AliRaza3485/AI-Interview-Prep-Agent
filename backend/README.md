# AI Interview Prep Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)
![LLM](https://img.shields.io/badge/LLM-Groq-orange)
![Status](https://img.shields.io/badge/status-active--development-yellow)

An agentic AI mock-interview coach. It takes a candidate's **resume** and a **job description**, figures out exactly where the candidate is weak relative to that specific job, runs an **adaptive mock interview** targeting those weak spots, and produces a **reasoning-based evaluation report** — not just a score.

---

## 1. Overview

Most "AI interview prep" tools generate a generic list of questions from a job title and grade answers with a single opaque score. That doesn't reflect how a real interview loop actually works: a good interviewer reads your resume against the JD first, decides what to probe, and adapts based on your answers.

**AI Interview Prep Agent** was built to close that gap, and to solve a real problem for its own author: preparing for job-hunting as a computer science student targeting AI/ML roles, without a human mock-interviewer on demand.

The system:

1. **Parses** a resume (PDF/DOCX) and a job description (raw text) into structured JSON.
2. Runs a **gap analysis** — comparing the two to find strengths, gaps, and partial matches specific to *this* candidate and *this* job.
3. **Generates tailored interview questions** that prioritize the candidate's actual weak spots and their real projects, mixing technical, behavioral, and project-deep-dive questions across difficulty levels.
4. Conducts a **turn-based interview loop**, evaluating each answer individually with reasoning (not just a number) as it goes.
5. Produces a final **report**: a difficulty-weighted score, a category breakdown, which JD gaps were actually addressed in the interview, and an LLM-synthesized narrative of strengths/weaknesses.

Every session is persisted, so a candidate can pick up an in-progress interview after a server restart or a dropped connection.

---

## 2. Architecture

```
                              ┌─────────────────────┐
                              │   Resume (PDF/DOCX)  │
                              │  + Job Description   │
                              └──────────┬───────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
           ┌───────────────────┐                   ┌───────────────────┐
           │   Resume Parser    │                   │     JD Parser      │
           │ extract_text() +   │                   │  structure_jd()    │
           │ structure_resume() │                   │                    │
           └──────────┬─────────┘                   └──────────┬─────────┘
                       │        structured JSON                │
                       └───────────────────┬────────────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │   LangGraph StateGraph    │
                              │  (InterviewState shared)  │
                              └─────────────────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                                     ▼
              ┌───────────────────┐               ┌─────────────────────────┐
              │   Analyzer Agent    │──gap_analysis→│  Question Generator Agent │
              │  strengths / gaps /  │               │ tailored, gap-prioritized │
              │  partial_matches     │               │   questions (8 default)   │
              └───────────────────┘               └─────────────┬─────────────┘
                                                                  │
                                                                  ▼
                                                  ┌───────────────────────────┐
                                                  │   Session created (SQLite) │
                                                  │  session_id + InterviewState│
                                                  └─────────────┬─────────────┘
                                                                  │
                                    ┌─────────────────────────────┘
                                    ▼
                     ┌──────────────────────────────────┐
                     │   Turn-Based Interview Loop         │
                     │   (per session, lock-guarded)        │
                     │                                      │
                     │   get_next_question()                │
                     │        │                             │
                     │        ▼                             │
                     │   candidate answers                  │
                     │        │                             │
                     │        ▼                             │
                     │   Evaluator Agent                    │
                     │   score + feedback + reasoning        │
                     │        │                             │
                     │        ▼                             │
                     │   state saved, advance to next Q      │
                     │        │                             │
                     │        └──── repeat until complete ───┘
                     └──────────────────┬───────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │   Report Generator Agent     │
                          │  - difficulty-weighted score  │
                          │  - category breakdown         │
                          │  - gaps addressed / still open│
                          │  - LLM narrative summary      │
                          └───────────────────────────┘
```

**Flow in one line:** `Resume/JD parsing → Gap Analysis → Question Generation → Turn-based Interview Loop → Report Generation`, with a SQLite-backed session sitting underneath the interview loop so state survives restarts and concurrent requests don't corrupt it.

### Module map

| Layer | Path | Responsibility |
|---|---|---|
| Parsers | `backend/parsers/` | File/text → structured JSON (resume, JD), plus the shared LLM client wrapper |
| Agents | `backend/agents/` | The four LLM-driven reasoning steps: analyze, generate questions, evaluate, report |
| Graph | `backend/graph/` | LangGraph `StateGraph` definition, shared `InterviewState`, turn-based loop helpers |
| API | `backend/api/` | FastAPI route layer — thin wrappers over parsers/agents/graph |
| Storage | `backend/session_store.py` | SQLite-backed, per-session-locked persistence for `InterviewState` |
| Entry point | `backend/main.py` | FastAPI app wiring, router registration, DB init, health check |

---

## 3. Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.11+ |
| API Framework | FastAPI |
| Agent Orchestration | LangGraph (`StateGraph`) |
| LLM Provider | Groq (`groq` SDK) |
| Resume Parsing | `pdfplumber` (PDF), `python-docx` (DOCX) |
| Persistence | SQLite (WAL mode) via `sqlite3` |
| Validation / Schemas | Pydantic (via FastAPI) |
| Config | `python-dotenv` |
| Testing | `pytest` |
| Server | `uvicorn` |
| Deployment | Docker on AWS EC2 (backend), Vercel (frontend) |

---

## 4. Design Decisions

This section explains the *why*, not just the *what* — the trade-offs considered while building this.

### Why a multi-agent pipeline instead of one big prompt?

A single "do everything" prompt (parse the resume, compare it to the JD, invent questions, and grade the candidate, all in one shot) sounds simpler, but it fails in practice for a few reasons:

- **Error isolation.** If gap analysis produces something slightly off, that's a small, debuggable problem. If it's baked into one giant prompt with question generation and evaluation, a bad gap analysis silently poisons every question that follows, and you have no way to tell which stage went wrong.
- **Focused, smaller prompts perform better.** An LLM asked to do one well-defined task (e.g., "compare resume to JD and list gaps") with a tight output schema is more reliable than one asked to juggle four tasks and produce four different nested schemas at once.
- **Independent evolution.** The evaluator's prompt can be tuned (e.g., stricter grading criteria) without touching how questions are generated. In a monolithic prompt, every change risks regressing unrelated behavior.
- **Testability.** Each agent (`analyzer_agent.py`, `question_generator_agent.py`, `evaluator_agent.py`, `report_generator_agent.py`) is a plain function that takes data + an injected LLM client and returns a dict. Each can be unit-tested with a mock client and a canned response — no real API calls needed (see `backend/tests/`).

The trade-off is more LLM calls (and latency) per session — acceptable here, since this is a guided, multi-step interview flow, not a single low-latency chat response.

### Why LangGraph `StateGraph` instead of just calling functions in sequence?

The analyze → generate-questions stage genuinely *is* a small pipeline with shared state, so it's a legitimate `StateGraph` (`backend/graph/interview_graph.py`): two nodes, one shared `InterviewState`, a linear edge between them. Using LangGraph here — rather than just two sequential function calls — buys:

- **A single, explicit state shape** (`InterviewState`, a `TypedDict`) that both nodes read/write, instead of passing loose arguments between functions and hoping they stay in sync.
- **A natural place to grow.** The turn-based interview loop and evaluation/report stages are structurally different (they're driven by user input arriving over multiple HTTP requests, not a one-shot pipeline run), so they're implemented as plain state-transition functions in `graph/interview_loop.py` operating on the *same* `InterviewState` shape — rather than forcing an inherently request/response, multi-turn process into graph nodes where it doesn't fit. This keeps the graph itself simple and honest about what's actually a DAG versus what's actually a stateful loop driven by an external client.
- **Room to extend the graph later** (e.g., conditional routing based on gap severity) without restructuring the whole pipeline.

### Why SQLite for session persistence instead of in-memory storage?

An in-memory dict (`sessions = {}`) is the obvious first approach, and it works — right up until:

- The server restarts (deploy, crash, EC2 instance recycling) and every in-progress interview is gone.
- You run more than one worker process, and a candidate's session lives on worker A while their next request lands on worker B, which has never heard of that `session_id`.

SQLite fixes both without introducing a separate service to run (Redis, Postgres) — it's a single file, built into the Python standard library, and easily "enough" for a solo-dev / early-stage project where the access pattern is simple key-value read-modify-write per session. `InterviewState` is serialized to a JSON `TEXT` column, which also decouples the storage layer from LangGraph's state shape: if the state schema changes, `session_store.py` doesn't need to.

### Why per-session locking?

FastAPI's sync routes run in a threadpool, so two requests genuinely can execute concurrently. `/interview/submit-answer` is a **read-modify-write** sequence (`load_session` → mutate in Python → `save_session`). Without a lock, two near-simultaneous requests for the *same* `session_id` (e.g., a flaky frontend that double-submits) would both read the same starting state, both mutate their own copy, and the second `save_session` call would silently overwrite the first candidate's answer and evaluation — a classic **lost update** race condition.

`session_store.py` solves this with:

1. **WAL mode + `busy_timeout`** on the SQLite connection, so concurrent writes to *different* sessions don't throw `database is locked` errors.
2. A **per-`session_id` `threading.Lock`** (`session_lock()`), so the entire load → mutate → save sequence for one session is atomic with respect to other requests for that *same* session — while requests for *different* sessions are completely unaffected and run in parallel.

This is deliberately a narrower fix than a global lock: it protects exactly the resource that's actually shared (one candidate's session state) without serializing unrelated candidates' interviews behind each other.

### Why dependency injection in the parsers?

`resume_parser.py` and `jd_parser.py` don't construct their own `GroqLLMClient` internally — every function that needs an LLM takes `llm_client` as a parameter, typed against a minimal `Protocol` (`.structure(prompt, model) -> str`). This means:

- **Tests never make real network calls.** A `MockLLMClient` that returns a canned string satisfies the same interface, so `backend/tests/` can fully exercise the parsing/validation logic (JSON fence stripping, schema defaults, malformed-response handling) deterministically and for free.
- **Text extraction and LLM structuring are separated.** `extract_text()` is pure and deterministic (testable with a fixture file, no API needed); `structure_resume()` / `structure_jd()` depend on an external API and are tested through the injected mock. Mixing these into one function would make the deterministic part impossible to test in isolation.
- **The provider is swappable.** Since agents/parsers only depend on the `.structure()` interface, switching from Groq to another provider later means writing one new client class — no changes to any agent or parser logic.

---

## 5. API Reference

All endpoints accept/return JSON except file uploads (`multipart/form-data`). Base URL: `http://localhost:8000`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/parse/resume` | Uploads a resume file (PDF/DOCX), extracts text, and returns it structured as JSON (skills, experience, projects, education). |
| `POST` | `/parse/jd` | Takes raw job description text and returns it structured as JSON (role, required/nice-to-have skills, responsibilities, keywords). |
| `POST` | `/analyze/gap` | Takes structured resume + JD data, returns a gap analysis: strengths, gaps, partial matches, and focus areas. |
| `POST` | `/analyze/questions` | Takes a gap analysis + resume + JD data, returns a tailored list of interview questions (technical / behavioral / project-deep-dive, mixed difficulty). |
| `POST` | `/interview/begin` | **Single entry point.** Uploads a resume file + raw JD text and runs the entire pipeline in one call: parse → gap analysis → question generation → session creation. Returns the first question. |
| `POST` | `/interview/start` | Same pipeline as `/interview/begin`, but takes already-structured resume + JD JSON instead of a raw file (useful if parsing was already done via `/parse/*`). |
| `POST` | `/interview/next-question` | Returns the current question for a given `session_id` (e.g., to resync a frontend after a refresh). |
| `POST` | `/interview/submit-answer` | Submits a candidate's answer for the current question: evaluates it, persists the result, and returns the next question (or completion status). |
| `POST` | `/interview/report` | Generates (or returns the cached) final report for a completed session: overall score, category breakdown, gaps addressed/still open, key strengths/weaknesses, and a written recommendation. |
| `GET` | `/health` | Basic health check; also reports whether `GROQ_API_KEY` is configured. |

---

## 6. Setup Instructions

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/keys)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AliRaza3485/AI-Interview-Prep-Agent.git   # download the repo locally
cd AI-Interview-Prep-Agent/backend                                     # all commands below run from backend/

# 2. Create and activate a virtual environment
python -m venv venv             # creates an isolated Python environment in ./venv
source venv/bin/activate        # activates it (Windows: venv\Scripts\activate)

# 3. Install dependencies
pip install -r requirements.txt   # installs FastAPI, LangGraph, Groq SDK, pytest, etc.

# 4. Configure environment variables
cp .env.example .env              # copies the template — creates your own local .env
# now open backend/.env and replace GROQ_API_KEY with your real Groq key
# (GROQ_MODEL already has a sensible default, no need to touch it unless you want a different model)

# 5. Run the server
uvicorn main:app --reload         # starts the FastAPI app with auto-reload on code changes
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

> `.env` is already covered by `.gitignore`, so your key won't be committed.

---

## 7. Testing

Tests live in `backend/tests/` and use mocked LLM clients (no real API calls, no API key required to run them).

```bash
cd backend    # tests use relative imports (e.g. `from graph.state import ...`),
              # so pytest must be run from inside backend/, not the repo root
pytest        # discovers and runs everything under backend/tests/
```

Run a single file, or with verbose per-test output:

```bash
pytest tests/test_interview_graph.py -v   # -v prints each test's name and pass/fail status
```

Coverage includes: resume/JD parsing and schema validation, the analyzer/question-generator/evaluator/report agents (via `MockLLMClient`), the LangGraph pipeline (`test_interview_graph.py`), and the turn-based interview loop (`test_interview_loop.py`).

---

## Roadmap / Status

This project is under active development as part of an ongoing AI/ML engineering portfolio. Frontend, deployment (Docker on AWS EC2 + Vercel), and further evaluation-quality improvements are in progress.
