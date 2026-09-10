from typing import TypedDict, List, Dict, Any


class InterviewState(TypedDict):
    """
    Shared state jo poore LangGraph ke through pass hota hai.
    Har node isi state ko read/update karta hai.
    """

    # Day 1 se aane wala input data
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]

    # Day 2 - Analyzer Agent aur Question Generator fill karenge
    gap_analysis: Dict[str, Any]
    questions: List[Dict[str, Any]]

    # Day 3+ - abhi ke liye reserved, interview loop mein use hoga
    current_question_idx: int
    answers: List[str]
    evaluations: List[Dict[str, Any]]

    # Day 4+ - final report
    report: Dict[str, Any]


def get_initial_state(resume_data: dict, jd_data: dict) -> InterviewState:
    """
    Graph ko run karne se pehle initial state banane ke liye helper.
    resume_data aur jd_data Day 1 ke parsers se aate hain.
    Baaki sab fields empty defaults ke saath initialize hoti hain.
    """
    return InterviewState(
        resume_data=resume_data,
        jd_data=jd_data,
        gap_analysis={},
        questions=[],
        current_question_idx=0,
        answers=[],
        evaluations=[],
        report={},
    )


def is_interview_complete(state: InterviewState) -> bool:
    """
    Batata hai ke saare questions ho chuke hain ya abhi baaki hain.
    True agar current_question_idx questions list ke size ke barabar ya zyada ho jaye.
    """
    return state["current_question_idx"] >= len(state["questions"])


def get_current_question(state: InterviewState) -> dict | None:
    """
    Abhi jo question active hai, wo return karta hai.
    Agar interview complete ho chuka ho (saare questions ho chuke), None return karta hai.
    """
    if is_interview_complete(state):
        return None
    return state["questions"][state["current_question_idx"]]


def submit_answer(state: InterviewState, answer: str) -> InterviewState:
    """
    User ka answer state mein save karta hai aur agle question ke liye
    current_question_idx aage badha deta hai.

    Note: Yeh sirf answer ko store karta hai. Evaluation (answer ka score/feedback)
    alag se Evaluator Agent karega (Step 2 mein banayenge).
    """
    if is_interview_complete(state):
        # Agar already complete ho chuka hai, kuch mat karo (safety check)
        return state

    state["answers"].append(answer)
    state["current_question_idx"] += 1
    return state
