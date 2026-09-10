from typing import Any, Dict, Optional

from graph.state import (
    InterviewState,
    get_current_question,
    is_interview_complete,
    submit_answer,
)
from agents.evaluator_agent import evaluate_answer


def get_next_question(state: InterviewState) -> Dict[str, Any]:
    """
    Frontend/API ko batata hai ke abhi konsa question dikhana hai.

    Returns:
        {
            "is_complete": bool,
            "question": dict or None,
            "question_number": int (1-indexed, human-friendly),
            "total_questions": int,
        }
    """
    complete = is_interview_complete(state)
    question = get_current_question(state)

    return {
        "is_complete": complete,
        "question": question,
        "question_number": state["current_question_idx"] + 1 if not complete else None,
        "total_questions": len(state["questions"]),
    }


def process_answer(
    state: InterviewState,
    answer: str,
    llm_client,
    model: str,
) -> InterviewState:
    """
    Ek turn poora karta hai: current question ka answer leta hai, evaluate karta hai,
    evaluation + answer state mein save karta hai, aur agle question pe move kar deta hai.

    Args:
        state: current InterviewState
        answer: candidate ka jawab (plain text)
        llm_client: GroqLLMClient instance (ya mock)
        model: Groq model name

    Returns:
        updated InterviewState (answers, evaluations, current_question_idx sab updated)
    """
    if is_interview_complete(state):
        # Safety: agar already complete ho chuka hai, kuch mat karo
        return state

    current_question = get_current_question(state)

    evaluation = evaluate_answer(
        question=current_question,
        answer=answer,
        jd_data=state["jd_data"],
        llm_client=llm_client,
        model=model,
    )

    # Evaluation ko save karo (answer ke saath alignment ke liye same index pe)
    state["evaluations"].append(evaluation)

    # Answer save karo aur current_question_idx aage badhao
    state = submit_answer(state, answer)

    return state


def get_interview_progress(state: InterviewState) -> Dict[str, Any]:
    """
    Session ka overall progress summary deta hai — dashboard/UI ke liye useful.

    Returns:
        {
            "answered": int,
            "total": int,
            "is_complete": bool,
        }
    """
    return {
        "answered": len(state["answers"]),
        "total": len(state["questions"]),
        "is_complete": is_interview_complete(state),
    }
