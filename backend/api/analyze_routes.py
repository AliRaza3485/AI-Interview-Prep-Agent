from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List

from config import settings
from parsers.llm_client import GroqLLMClient
from agents.analyzer_agent import analyze_gap
from agents.question_generator_agent import generate_questions, DEFAULT_QUESTION_COUNT

router = APIRouter()

# Day 1 ke parse_routes.py jaisa hi single shared client instance
llm_client = GroqLLMClient(api_key=settings.GROQ_API_KEY)


# ---------- Request/Response Schemas ----------


class GapAnalysisRequest(BaseModel):
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]


class GapAnalysisResponse(BaseModel):
    strengths: List[str]
    gaps: List[str]
    partial_matches: List[str]
    focus_areas: List[str]


class QuestionGenerationRequest(BaseModel):
    gap_analysis: Dict[str, Any]
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]
    question_count: int = DEFAULT_QUESTION_COUNT


class Question(BaseModel):
    question: str
    category: str
    difficulty: str
    targets: str


class QuestionGenerationResponse(BaseModel):
    questions: List[Question]


# ---------- Routes ----------


@router.post("/analyze/gap", response_model=GapAnalysisResponse)
def analyze_gap_route(payload: GapAnalysisRequest):
    """
    Resume ka structured data + JD ka structured data lekar
    gap analysis (strengths, gaps, partial_matches, focus_areas) return karta hai.
    """
    result = analyze_gap(
        resume_data=payload.resume_data,
        jd_data=payload.jd_data,
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
    )
    return result


@router.post("/analyze/questions", response_model=QuestionGenerationResponse)
def generate_questions_route(payload: QuestionGenerationRequest):
    """
    Gap analysis + resume data + JD data lekar tailored interview questions
    (category + difficulty tag ke saath) generate karta hai.
    """
    questions = generate_questions(
        gap_analysis=payload.gap_analysis,
        resume_data=payload.resume_data,
        jd_data=payload.jd_data,
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
        question_count=payload.question_count,
    )
    return {"questions": questions}
