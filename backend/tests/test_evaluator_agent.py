import json

from agents.evaluator_agent import evaluate_answer

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    def __init__(self, response_text: str = "", raise_exception: bool = False):
        self.response_text = response_text
        self.raise_exception = raise_exception
        self.last_prompt = None
        self.last_model = None

    def structure(self, prompt: str, model: str) -> str:
        self.last_prompt = prompt
        self.last_model = model
        if self.raise_exception:
            raise RuntimeError("Simulated Groq API failure")
        return self.response_text


SAMPLE_QUESTION = {
    "question": "Explain how Docker containers differ from a VM.",
    "category": "technical",
    "difficulty": "medium",
    "targets": "Docker",
}

SAMPLE_JD = {
    "role_title": "Backend Engineer",
    "required_skills": ["Python", "Docker"],
}


# ---------- Test 1: Happy path ----------


def test_evaluate_answer_happy_path():
    fake_response = json.dumps(
        {
            "score": 7,
            "feedback": "Good conceptual understanding, but missed a few details.",
            "strengths_shown": ["Understands isolation concept"],
            "improvement_areas": ["Mention image layering"],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = evaluate_answer(
        SAMPLE_QUESTION,
        "Docker uses containers which share the host OS kernel, unlike VMs.",
        SAMPLE_JD,
        mock_client,
        FAKE_MODEL,
    )

    assert result["score"] == 7
    assert "isolation" in result["strengths_shown"][0].lower()
    assert mock_client.last_model == FAKE_MODEL


# ---------- Test 2: Empty answer skips the LLM call entirely ----------


def test_evaluate_answer_empty_answer():
    mock_client = MockLLMClient(response_text="should not be used")

    result = evaluate_answer(SAMPLE_QUESTION, "", SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result["score"] == 0
    assert mock_client.last_prompt is None  # LLM ko call hi nahi hona chahiye


def test_evaluate_answer_whitespace_only_answer():
    mock_client = MockLLMClient(response_text="should not be used")

    result = evaluate_answer(SAMPLE_QUESTION, "   ", SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result["score"] == 0
    assert mock_client.last_prompt is None


# ---------- Test 3: Malformed JSON from LLM ----------


def test_evaluate_answer_malformed_json():
    mock_client = MockLLMClient(response_text="not valid json {{{")

    result = evaluate_answer(
        SAMPLE_QUESTION, "Some answer text", SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result["score"] == 0
    assert result["feedback"] != ""


# ---------- Test 4: LLM raises an exception ----------


def test_evaluate_answer_llm_exception():
    mock_client = MockLLMClient(raise_exception=True)

    result = evaluate_answer(
        SAMPLE_QUESTION, "Some answer text", SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result["score"] == 0


# ---------- Test 5: Score gets clamped if LLM returns an out-of-range value ----------


def test_evaluate_answer_score_clamped_above_max():
    fake_response = json.dumps(
        {
            "score": 25,  # LLM ne galti se range se bahar ka score de diya
            "feedback": "Excellent answer.",
            "strengths_shown": ["Great depth"],
            "improvement_areas": [],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = evaluate_answer(
        SAMPLE_QUESTION, "A very detailed answer", SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result["score"] == 10  # clamp ho ke max 10 hona chahiye


def test_evaluate_answer_score_clamped_below_min():
    fake_response = json.dumps(
        {
            "score": -5,
            "feedback": "Poor answer.",
            "strengths_shown": [],
            "improvement_areas": ["Everything"],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = evaluate_answer(
        SAMPLE_QUESTION, "Bad answer", SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result["score"] == 0  # clamp ho ke min 0 hona chahiye


# ---------- Test 6: Score as a non-numeric type falls back to 0 ----------


def test_evaluate_answer_non_numeric_score():
    fake_response = json.dumps(
        {
            "score": "seven",  # LLM ne string de di, number nahi
            "feedback": "Decent answer.",
            "strengths_shown": [],
            "improvement_areas": [],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = evaluate_answer(
        SAMPLE_QUESTION, "Some answer", SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result["score"] == 0
