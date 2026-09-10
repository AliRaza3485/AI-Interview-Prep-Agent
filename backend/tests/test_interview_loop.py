import json

from graph.state import get_initial_state
from graph.interview_loop import (
    get_next_question,
    process_answer,
    get_interview_progress,
)

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    """Evaluator internally calls llm_client.structure(prompt, model)."""

    def __init__(self, response_text: str = "", raise_exception: bool = False):
        self.response_text = response_text
        self.raise_exception = raise_exception
        self.prompts = []

    def structure(self, prompt: str, model: str) -> str:
        self.prompts.append(prompt)
        if self.raise_exception:
            raise RuntimeError("Simulated failure")
        return self.response_text


SAMPLE_RESUME = {"skills": ["Python"]}
SAMPLE_JD = {"role_title": "Backend Engineer", "required_skills": ["Python", "Docker"]}

SAMPLE_QUESTIONS = [
    {
        "question": "Explain Docker vs VM.",
        "category": "technical",
        "difficulty": "medium",
        "targets": "Docker",
    },
    {
        "question": "Tell me about a challenging bug you fixed.",
        "category": "behavioral",
        "difficulty": "easy",
        "targets": "Problem solving",
    },
]


def _build_state_with_questions():
    """
    get_initial_state() questions ko empty rakhta hai (Day 2 ka kaam),
    isliye yahan manually questions inject karte hain taake interview_loop
    ko isolate karke test kar sakein (Day 2 pipeline dobara chalane ki zaroorat nahi).
    """
    state = get_initial_state(SAMPLE_RESUME, SAMPLE_JD)
    state["questions"] = SAMPLE_QUESTIONS
    return state


FAKE_EVALUATION = json.dumps(
    {
        "score": 6,
        "feedback": "Reasonable answer.",
        "strengths_shown": ["Basic understanding"],
        "improvement_areas": ["More depth needed"],
    }
)


# ---------- get_next_question ----------


def test_get_next_question_returns_first_question():
    state = _build_state_with_questions()

    result = get_next_question(state)

    assert result["is_complete"] is False
    assert result["question"]["question"] == "Explain Docker vs VM."
    assert result["question_number"] == 1
    assert result["total_questions"] == 2


def test_get_next_question_when_all_answered():
    state = _build_state_with_questions()
    state["current_question_idx"] = 2  # dono questions ho chuke

    result = get_next_question(state)

    assert result["is_complete"] is True
    assert result["question"] is None
    assert result["question_number"] is None


# ---------- process_answer ----------


def test_process_answer_stores_answer_and_advances_index():
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)

    state = process_answer(
        state, "Docker shares the host kernel.", mock_client, FAKE_MODEL
    )

    assert state["answers"] == ["Docker shares the host kernel."]
    assert state["current_question_idx"] == 1


def test_process_answer_appends_evaluation():
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)

    state = process_answer(state, "Some answer", mock_client, FAKE_MODEL)

    assert len(state["evaluations"]) == 1
    assert state["evaluations"][0]["score"] == 6


def test_process_answer_evaluates_correct_question_before_advancing():
    """
    Critical test: confirm karta hai ke pehle question ka jawab dete waqt,
    prompt mein PEHLA question hi jaye (dusra nahi), chahe index badh chuka ho baad mein.
    """
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)

    process_answer(state, "My answer about Docker", mock_client, FAKE_MODEL)

    sent_prompt = mock_client.prompts[0]
    assert "Explain Docker vs VM." in sent_prompt
    assert "Tell me about a challenging bug" not in sent_prompt


def test_process_answer_does_nothing_when_already_complete():
    state = _build_state_with_questions()
    state["current_question_idx"] = 2  # already complete
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)

    state = process_answer(state, "Late answer", mock_client, FAKE_MODEL)

    assert state["answers"] == []  # kuch add nahi hua
    assert state["evaluations"] == []  # LLM call bhi nahi hui
    assert mock_client.prompts == []


def test_process_answer_full_two_question_flow():
    """
    Poora 2-question interview simulate karta hai: dono answers submit karo,
    aakhir mein is_interview_complete True hona chahiye.
    """
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)

    state = process_answer(state, "Answer 1", mock_client, FAKE_MODEL)
    state = process_answer(state, "Answer 2", mock_client, FAKE_MODEL)

    assert len(state["answers"]) == 2
    assert len(state["evaluations"]) == 2
    assert get_next_question(state)["is_complete"] is True


# ---------- get_interview_progress ----------


def test_get_interview_progress_partial():
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)
    state = process_answer(state, "Answer 1", mock_client, FAKE_MODEL)

    progress = get_interview_progress(state)

    assert progress == {"answered": 1, "total": 2, "is_complete": False}


def test_get_interview_progress_complete():
    state = _build_state_with_questions()
    mock_client = MockLLMClient(response_text=FAKE_EVALUATION)
    state = process_answer(state, "Answer 1", mock_client, FAKE_MODEL)
    state = process_answer(state, "Answer 2", mock_client, FAKE_MODEL)

    progress = get_interview_progress(state)

    assert progress == {"answered": 2, "total": 2, "is_complete": True}
