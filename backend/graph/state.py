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
