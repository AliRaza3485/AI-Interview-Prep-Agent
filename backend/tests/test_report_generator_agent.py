import json

from agents.report_generator_agent import (
    generate_report,
    _compute_overall_score,
    _compute_readiness_level,
    _compute_category_breakdown,
    _match_gaps,
    _aggregate_raw_feedback,
)

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    def __init__(self, response_text: str = "", raise_exception: bool = False):
        self.response_text = response_text
        self.raise_exception = raise_exception
        self.last_prompt = None

    def structure(self, prompt: str, model: str) -> str:
        self.last_prompt = prompt
        if self.raise_exception:
            raise RuntimeError("Simulated failure")
        return self.response_text


SAMPLE_QUESTIONS = [
    {
        "question": "Q1",
        "category": "technical",
        "difficulty": "easy",
        "targets": "Python",
    },
    {
        "question": "Q2",
        "category": "technical",
        "difficulty": "hard",
        "targets": "Docker",
    },
    {
        "question": "Q3",
        "category": "behavioral",
        "difficulty": "medium",
        "targets": "Teamwork",
    },
]

SAMPLE_EVALUATIONS = [
    {
        "score": 8,
        "feedback": "Good",
        "strengths_shown": ["Clear explanation"],
        "improvement_areas": [],
    },
    {
        "score": 4,
        "feedback": "Weak",
        "strengths_shown": [],
        "improvement_areas": ["Needs Docker depth"],
    },
    {
        "score": 9,
        "feedback": "Great",
        "strengths_shown": ["Clear explanation"],
        "improvement_areas": ["Be concise"],
    },
]

SAMPLE_ANSWERS = ["Answer 1", "Answer 2", "Answer 3"]

SAMPLE_GAP_ANALYSIS = {
    "strengths": ["Python"],
    "gaps": ["Docker", "Kubernetes"],
    "partial_matches": [],
    "focus_areas": ["Containerization"],
}


# ---------- _compute_overall_score ----------


def test_overall_score_weighted_average():
    # weights: easy=1, hard=3, medium=2 -> (8*1 + 4*3 + 9*2) / (1+3+2) = 38/6 = 6.33 -> 6.3
    result = _compute_overall_score(SAMPLE_QUESTIONS, SAMPLE_EVALUATIONS)
    assert result == 6.3


def test_overall_score_empty_inputs():
    assert _compute_overall_score([], []) == 0.0
    assert _compute_overall_score(SAMPLE_QUESTIONS, []) == 0.0


# ---------- _compute_readiness_level ----------


def test_readiness_level_ready():
    assert _compute_readiness_level(8.5) == "Ready for Real Interviews"
    assert _compute_readiness_level(8.0) == "Ready for Real Interviews"


def test_readiness_level_almost_ready():
    assert _compute_readiness_level(6.0) == "Almost Ready"
    assert _compute_readiness_level(5.0) == "Almost Ready"


def test_readiness_level_needs_practice():
    assert _compute_readiness_level(4.9) == "Needs More Practice"
    assert _compute_readiness_level(0.0) == "Needs More Practice"


# ---------- _compute_category_breakdown ----------


def test_category_breakdown():
    result = _compute_category_breakdown(SAMPLE_QUESTIONS, SAMPLE_EVALUATIONS)

    assert result["technical"]["average_score"] == 6.0  # (8+4)/2
    assert result["technical"]["questions_count"] == 2
    assert result["behavioral"]["average_score"] == 9.0
    assert result["behavioral"]["questions_count"] == 1


# ---------- _match_gaps ----------


def test_match_gaps_addressed_and_open():
    gaps_addressed, gaps_still_open = _match_gaps(
        SAMPLE_GAP_ANALYSIS, SAMPLE_QUESTIONS, SAMPLE_EVALUATIONS
    )
    # "Docker" gap matched to Q2 (score 4) -> below threshold 6 -> still open
    assert "Docker" in gaps_still_open
    # "Kubernetes" gap has no matching question at all -> still open
    assert "Kubernetes" in gaps_still_open
    assert gaps_addressed == []


def test_match_gaps_addressed_when_score_high():
    good_evaluations = [
        {"score": 8, "feedback": "", "strengths_shown": [], "improvement_areas": []},
        {"score": 9, "feedback": "", "strengths_shown": [], "improvement_areas": []},
        {"score": 8, "feedback": "", "strengths_shown": [], "improvement_areas": []},
    ]
    gaps_addressed, gaps_still_open = _match_gaps(
        SAMPLE_GAP_ANALYSIS, SAMPLE_QUESTIONS, good_evaluations
    )
    assert "Docker" in gaps_addressed
    assert "Kubernetes" in gaps_still_open  # no question targets it at all


def test_match_gaps_empty_gap_analysis():
    gaps_addressed, gaps_still_open = _match_gaps(
        {}, SAMPLE_QUESTIONS, SAMPLE_EVALUATIONS
    )
    assert gaps_addressed == []
    assert gaps_still_open == []


# ---------- _aggregate_raw_feedback ----------


def test_aggregate_raw_feedback_dedupes():
    strengths, weaknesses = _aggregate_raw_feedback(SAMPLE_EVALUATIONS)
    # "Clear explanation" appears twice in evaluations but should appear once
    assert strengths.count("Clear explanation") == 1
    assert "Needs Docker depth" in weaknesses
    assert "Be concise" in weaknesses


# ---------- generate_report (full integration) ----------


def test_generate_report_happy_path():
    fake_narrative = json.dumps(
        {
            "key_strengths": ["Explains concepts clearly"],
            "key_weaknesses": ["Needs deeper Docker knowledge"],
            "recommendation_summary": "Focus on containerization before your next interview.",
        }
    )
    mock_client = MockLLMClient(response_text=fake_narrative)

    report = generate_report(
        SAMPLE_QUESTIONS,
        SAMPLE_ANSWERS,
        SAMPLE_EVALUATIONS,
        SAMPLE_GAP_ANALYSIS,
        mock_client,
        FAKE_MODEL,
    )

    assert report["overall_score"] == 6.3
    assert report["readiness_level"] == "Almost Ready"
    assert len(report["question_breakdown"]) == 3
    assert report["key_strengths"] == ["Explains concepts clearly"]
    assert "Docker" in report["gaps_still_open"]


def test_generate_report_no_evaluations_skips_llm():
    mock_client = MockLLMClient(response_text="should not be used")

    report = generate_report([], [], [], {}, mock_client, FAKE_MODEL)

    assert report["overall_score"] == 0.0
    assert report["readiness_level"] == "Needs More Practice"
    assert mock_client.last_prompt is None


def test_generate_report_llm_failure_still_returns_computed_fields():
    mock_client = MockLLMClient(raise_exception=True)

    report = generate_report(
        SAMPLE_QUESTIONS,
        SAMPLE_ANSWERS,
        SAMPLE_EVALUATIONS,
        SAMPLE_GAP_ANALYSIS,
        mock_client,
        FAKE_MODEL,
    )

    # LLM fail hone ke bawajood, deterministic fields sahi milne chahiye
    assert report["overall_score"] == 6.3
    assert report["category_breakdown"]["technical"]["questions_count"] == 2
    # Sirf narrative fields empty/fallback honi chahiye
    assert report["key_strengths"] == []


def test_generate_report_question_breakdown_matches_data():
    mock_client = MockLLMClient(
        response_text=json.dumps(
            {"key_strengths": [], "key_weaknesses": [], "recommendation_summary": "ok"}
        )
    )

    report = generate_report(
        SAMPLE_QUESTIONS,
        SAMPLE_ANSWERS,
        SAMPLE_EVALUATIONS,
        SAMPLE_GAP_ANALYSIS,
        mock_client,
        FAKE_MODEL,
    )

    first_row = report["question_breakdown"][0]
    assert first_row["question"] == "Q1"
    assert first_row["answer"] == "Answer 1"
    assert first_row["score"] == 8
