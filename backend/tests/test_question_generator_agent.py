import json

from agents.question_generator_agent import generate_questions

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    """
    Real GroqLLMClient jaisa hi interface: .structure(prompt, model) -> str
    """

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


# ---------- Sample data ----------

SAMPLE_GAP_ANALYSIS = {
    "strengths": ["Python", "FastAPI"],
    "gaps": ["Docker", "Kubernetes"],
    "partial_matches": ["SQL"],
    "focus_areas": ["Containerization", "System design"],
}

SAMPLE_RESUME = {
    "skills": ["Python", "FastAPI", "SQL"],
    "experience": ["Backend developer at XYZ for 2 years"],
    "projects": ["Built a REST API for inventory management"],
    "education": ["BS Computer Science"],
}

SAMPLE_JD = {
    "role_title": "Backend Engineer",
    "role_level": "Mid",
    "required_skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
    "nice_to_have_skills": ["AWS"],
    "responsibilities": ["Design and maintain backend services"],
    "keywords": ["microservices", "REST API"],
}


def _valid_question(
    question="Explain Docker vs a VM.",
    category="technical",
    difficulty="medium",
    targets="Docker",
):
    return {
        "question": question,
        "category": category,
        "difficulty": difficulty,
        "targets": targets,
    }


# ---------- Test 1: Happy path ----------


def test_generate_questions_happy_path():
    fake_questions = [
        _valid_question("Explain Docker vs a VM.", "technical", "medium", "Docker"),
        _valid_question(
            "Tell me about the inventory API project.",
            "project_deep_dive",
            "easy",
            "Resume project",
        ),
        _valid_question(
            "How do you handle disagreement in a team?",
            "behavioral",
            "easy",
            "Soft skills",
        ),
    ]
    mock_client = MockLLMClient(response_text=json.dumps(fake_questions))

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS, SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert len(result) == 3
    assert result[0]["category"] == "technical"
    assert result[1]["category"] == "project_deep_dive"
    assert mock_client.last_model == FAKE_MODEL


# ---------- Test 2: All inputs empty ----------


def test_generate_questions_all_inputs_empty():
    mock_client = MockLLMClient(response_text="should not be used")

    result = generate_questions({}, {}, {}, mock_client, FAKE_MODEL)

    assert result == []
    assert mock_client.last_prompt is None


# ---------- Test 3: Malformed JSON from LLM ----------


def test_generate_questions_malformed_json():
    mock_client = MockLLMClient(response_text="not valid json [[[")

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS, SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result == []


# ---------- Test 4: LLM raises exception ----------


def test_generate_questions_llm_exception():
    mock_client = MockLLMClient(raise_exception=True)

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS, SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result == []


# ---------- Test 5: LLM returns a dict instead of a list ----------


def test_generate_questions_response_not_a_list():
    mock_client = MockLLMClient(response_text=json.dumps({"question": "oops"}))

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS, SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL
    )

    assert result == []


# ---------- Test 6: Invalid category/difficulty gets filtered out ----------


def test_generate_questions_filters_invalid_entries():
    fake_questions = [
        _valid_question("Valid question here.", "technical", "medium", "Docker"),
        {
            "question": "Bad category question.",
            "category": "not_a_real_category",
            "difficulty": "medium",
            "targets": "x",
        },
        {
            "question": "Bad difficulty question.",
            "category": "technical",
            "difficulty": "impossible",
            "targets": "x",
        },
        {
            # missing "question" key entirely
            "category": "technical",
            "difficulty": "easy",
            "targets": "x",
        },
    ]
    mock_client = MockLLMClient(response_text=json.dumps(fake_questions))

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS, SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL
    )

    # sirf pehla valid question bachna chahiye, baaki 3 invalid skip ho jaein
    assert len(result) == 1
    assert result[0]["question"] == "Valid question here."


# ---------- Test 7: Custom question_count is passed into the prompt ----------


def test_generate_questions_custom_count_in_prompt():
    fake_questions = [_valid_question() for _ in range(5)]
    mock_client = MockLLMClient(response_text=json.dumps(fake_questions))

    result = generate_questions(
        SAMPLE_GAP_ANALYSIS,
        SAMPLE_RESUME,
        SAMPLE_JD,
        mock_client,
        FAKE_MODEL,
        question_count=5,
    )

    assert len(result) == 5
    # prompt mein "5" mention hona chahiye taake LLM ko sahi count pata chale
    assert "5" in mock_client.last_prompt
