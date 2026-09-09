import json
import pytest

from agents.analyzer_agent import analyze_gap, _empty_gap_analysis

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    """
    Real GroqLLMClient jaisa hi interface: .structure(prompt, model) -> str
    Lekin real API call nahi karta, seedha ek fixed response return karta hai
    jo hum test mein control karte hain.
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


# ---------- Sample data used across tests ----------

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


# ---------- Test 1: Happy path ----------


def test_analyze_gap_happy_path():
    fake_response = json.dumps(
        {
            "strengths": ["Python", "FastAPI"],
            "gaps": ["Docker", "Kubernetes"],
            "partial_matches": ["SQL vs advanced database design"],
            "focus_areas": ["Containerization experience", "System design depth"],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = analyze_gap(SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL)

    assert set(result.keys()) == {"strengths", "gaps", "partial_matches", "focus_areas"}
    assert "Python" in result["strengths"]
    assert "Docker" in result["gaps"]
    assert len(result["focus_areas"]) == 2
    # confirm llm_client was actually called with the right model
    assert mock_client.last_model == FAKE_MODEL
    assert mock_client.last_prompt is not None


# ---------- Test 2: Empty resume and JD ----------


def test_analyze_gap_empty_resume_and_jd():
    mock_client = MockLLMClient(response_text="should not be used")

    result = analyze_gap({}, {}, mock_client, FAKE_MODEL)

    assert result == _empty_gap_analysis()
    # LLM ko call hi nahi hona chahiye tha
    assert mock_client.last_prompt is None


# ---------- Test 3: Malformed JSON from LLM ----------


def test_analyze_gap_malformed_json():
    mock_client = MockLLMClient(response_text="this is not valid json {{{")

    result = analyze_gap(SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result == _empty_gap_analysis()


# ---------- Test 4: LLM raises an exception ----------


def test_analyze_gap_llm_exception():
    mock_client = MockLLMClient(raise_exception=True)

    result = analyze_gap(SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result == _empty_gap_analysis()


# ---------- Test 5: LLM wraps JSON in markdown fences ----------


def test_analyze_gap_strips_markdown_fences():
    fake_json = {
        "strengths": ["Python"],
        "gaps": ["Kubernetes"],
        "partial_matches": [],
        "focus_areas": ["Kubernetes fundamentals"],
    }
    fenced_response = f"```json\n{json.dumps(fake_json)}\n```"
    mock_client = MockLLMClient(response_text=fenced_response)

    result = analyze_gap(SAMPLE_RESUME, SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result["strengths"] == ["Python"]
    assert result["gaps"] == ["Kubernetes"]


# ---------- Test 6: One resume field missing entirely ----------


def test_analyze_gap_partial_resume_data():
    partial_resume = {"skills": ["Python"]}  # experience/projects/education missing
    fake_response = json.dumps(
        {
            "strengths": ["Python"],
            "gaps": ["FastAPI", "Docker", "Kubernetes"],
            "partial_matches": [],
            "focus_areas": ["Overall backend experience depth"],
        }
    )
    mock_client = MockLLMClient(response_text=fake_response)

    result = analyze_gap(partial_resume, SAMPLE_JD, mock_client, FAKE_MODEL)

    assert result["strengths"] == ["Python"]
    assert "FastAPI" in result["gaps"]
