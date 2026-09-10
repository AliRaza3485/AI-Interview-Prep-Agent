import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from parsers.llm_client import GroqLLMClient
from graph.state import InterviewState, get_initial_state
from graph.interview_graph import app_graph
from graph.interview_loop import (
    get_next_question,
    process_answer,
    get_interview_progress,
    finalize_interview,
)

router = APIRouter()

# Shared LLM client, jaisa analyze_routes.py mein hai
llm_client = GroqLLMClient(api_key=settings.GROQ_API_KEY)

# Simple in-memory session store.
# Key: session_id (str), Value: InterviewState
# NOTE: Yeh server restart hone pe khatam ho jata hai. Production mein isse
# database ya Redis se replace karna hoga, abhi Day 3 ke liye kaafi hai.
SESSIONS: Dict[str, InterviewState] = {}


# ---------- Request/Response Schemas ----------


class StartInterviewRequest(BaseModel):
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]


class StartInterviewResponse(BaseModel):
    session_id: str
    is_complete: bool
    question: Optional[Dict[str, Any]]
    question_number: Optional[int]
    total_questions: int
    gap_analysis: Dict[str, Any]


class SessionIdRequest(BaseModel):
    session_id: str


class NextQuestionResponse(BaseModel):
    is_complete: bool
    question: Optional[Dict[str, Any]]
    question_number: Optional[int]
    total_questions: int


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str


class SubmitAnswerResponse(BaseModel):
    evaluation: Dict[str, Any]
    is_complete: bool
    next_question: Optional[Dict[str, Any]]
    question_number: Optional[int]
    total_questions: int


class ReportResponse(BaseModel):
    overall_score: float
    readiness_level: str
    category_breakdown: Dict[str, Any]
    gaps_addressed: List[str]
    gaps_still_open: List[str]
    key_strengths: List[str]
    key_weaknesses: List[str]
    recommendation_summary: str
    question_breakdown: List[Dict[str, Any]]


# ---------- Helper ----------


def _get_session_or_404(session_id: str) -> InterviewState:
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


# ---------- Routes ----------


@router.post("/interview/start", response_model=StartInterviewResponse)
def start_interview(payload: StartInterviewRequest):
    """
    Resume + JD data leke poori Day 2 pipeline chalata hai (gap analysis + questions),
    ek naya interview session banata hai, aur pehla question return karta hai.
    """
    initial_state = get_initial_state(payload.resume_data, payload.jd_data)
    result_state = app_graph.invoke(initial_state)

    if not result_state["questions"]:
        raise HTTPException(
            status_code=422,
            detail="Could not generate interview questions from the given data.",
        )

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = result_state

    next_q = get_next_question(result_state)

    return {
        "session_id": session_id,
        "is_complete": next_q["is_complete"],
        "question": next_q["question"],
        "question_number": next_q["question_number"],
        "total_questions": next_q["total_questions"],
        "gap_analysis": result_state["gap_analysis"],
    }


@router.post("/interview/next-question", response_model=NextQuestionResponse)
def next_question(payload: SessionIdRequest):
    """
    Diye gaye session ka current question dobara return karta hai
    (jaise agar frontend refresh ho jaye).
    """
    state = _get_session_or_404(payload.session_id)
    return get_next_question(state)


@router.post("/interview/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer_route(payload: SubmitAnswerRequest):
    """
    Candidate ka answer submit karta hai: evaluate karta hai, state update karta hai,
    aur agla question (ya completion status) return karta hai.
    """
    state = _get_session_or_404(payload.session_id)

    if get_interview_progress(state)["is_complete"]:
        raise HTTPException(status_code=400, detail="Interview already complete.")

    # Kitne evaluations pehle se hain, yeh yaad rakho taake naya wala pehchan sakein
    evaluations_before = len(state["evaluations"])

    state = process_answer(
        state=state,
        answer=payload.answer,
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
    )

    # process_answer() ne jo naya evaluation abhi add kiya, wahi humein response mein chahiye
    latest_evaluation = state["evaluations"][evaluations_before]

    SESSIONS[payload.session_id] = state

    next_q = get_next_question(state)

    return {
        "evaluation": latest_evaluation,
        "is_complete": next_q["is_complete"],
        "next_question": next_q["question"],
        "question_number": next_q["question_number"],
        "total_questions": next_q["total_questions"],
    }


@router.post("/interview/report", response_model=ReportResponse)
def get_interview_report(payload: SessionIdRequest):
    """
    Diye gaye session ka final report generate/return karta hai.
    Agar interview abhi complete nahi hua, HTTP 400 error deta hai.
    """
    state = _get_session_or_404(payload.session_id)

    report = finalize_interview(
        state=state,
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
    )

    if report is None:
        progress = get_interview_progress(state)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Interview not yet complete. "
                f"{progress['answered']} of {progress['total']} questions answered."
            ),
        )

    # state["report"] finalize_interview() ke andar already set ho chuka hai,
    # session store mein wapas save kar dete hain taake future calls cached mile
    SESSIONS[payload.session_id] = state

    return report
