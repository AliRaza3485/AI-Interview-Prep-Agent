import json

import graph.interview_graph as interview_graph_module
from graph.state import get_initial_state
from graph.interview_graph import build_graph

FAKE_MODEL = "openai/gpt-oss-120b"


class MockLLMClient:
    """
    .structure(prompt, model) -> str jaisa real GroqLLMClient.
    Do alag responses de sakta hai: pehli call (analyze) ke liye ek,
    doosri call (generate_questions) ke liye doosra — call_count se track karte hain.
    """

    def __init__(self, gap_response: str, questions_response: str):
        self.gap_response = gap_response
        self.questions_response = questions_response
        self.call_count = 0
        self.prompts = []  # har call ka prompt store karte hain, inspection ke liye

    def structure(self, prompt: str, model: str) -> str:
        self.prompts.append(prompt)
        self.call_count += 1
        # Pehli call analyze_node se aati hai, doosri generate_questions_node se
        if self.call_count == 1:
            return self.gap_response
        return self.questions_response


SAMPLE_RESUME = {
    "skills": ["Python", "FastAPI"],
    "experience": ["Backend developer for 2 years"],
    "projects": ["Inventory management REST API"],
    "education": ["BS Computer Science"],
}

SAMPLE_JD = {
    "role_title": "Backend Engineer",
    "role_level": "Mid",
    "required_skills": ["Python", "FastAPI", "Docker"],
    "nice_to_have_skills": ["AWS"],
    "responsibilities": ["Maintain backend services"],
    "keywords": ["REST API"],
}

FAKE_GAP_ANALYSIS = {
    "strengths": ["Python", "FastAPI"],
    "gaps": ["Docker"],
    "partial_matches": [],
    "focus_areas": ["Containerization basics"],
}

FAKE_QUESTIONS = [
    {
        "question": "Explain how Docker containers differ from virtual machines.",
        "category": "technical",
        "difficulty": "medium",
        "targets": "Docker",
    },
    {
        "question": "Walk me through the inventory management API you built.",
        "category": "project_deep_dive",
        "difficulty": "easy",
        "targets": "Resume project",
    },
]


def test_graph_happy_path(monkeypatch):
    mock_client = MockLLMClient(
        gap_response=json.dumps(FAKE_GAP_ANALYSIS),
        questions_response=json.dumps(FAKE_QUESTIONS),
    )
    # interview_graph module ke andar wale llm_client ko mock se replace karo
    monkeypatch.setattr(interview_graph_module, "llm_client", mock_client)

    app_graph = build_graph()
    initial_state = get_initial_state(SAMPLE_RESUME, SAMPLE_JD)

    final_state = app_graph.invoke(initial_state)

    assert final_state["gap_analysis"]["gaps"] == ["Docker"]
    assert len(final_state["questions"]) == 2
    assert final_state["questions"][0]["category"] == "technical"
    # dono nodes ne LLM ko call kiya hona chahiye
    assert mock_client.call_count == 2


def test_graph_state_flows_correctly(monkeypatch):
    """
    Confirm karta hai ke analyze_node ka output (gap_analysis) generate_questions_node
    tak sahi pahuncha — gap_analysis ka data doosri call ke prompt mein mojood hona chahiye.
    """
    mock_client = MockLLMClient(
        gap_response=json.dumps(FAKE_GAP_ANALYSIS),
        questions_response=json.dumps(FAKE_QUESTIONS),
    )
    monkeypatch.setattr(interview_graph_module, "llm_client", mock_client)

    app_graph = build_graph()
    initial_state = get_initial_state(SAMPLE_RESUME, SAMPLE_JD)

    app_graph.invoke(initial_state)

    # doosri call ka prompt (index 1) generate_questions_node se aaya
    second_prompt = mock_client.prompts[1]
    assert "Docker" in second_prompt  # gap_analysis ka "gaps" data isme hona chahiye
    assert "Containerization basics" in second_prompt  # focus_areas bhi


def test_graph_preserves_resume_and_jd_data(monkeypatch):
    """
    Confirm karta hai ke poore graph ke through resume_data aur jd_data
    state mein intact rehte hain (overwrite nahi hote).
    """
    mock_client = MockLLMClient(
        gap_response=json.dumps(FAKE_GAP_ANALYSIS),
        questions_response=json.dumps(FAKE_QUESTIONS),
    )
    monkeypatch.setattr(interview_graph_module, "llm_client", mock_client)

    app_graph = build_graph()
    initial_state = get_initial_state(SAMPLE_RESUME, SAMPLE_JD)

    final_state = app_graph.invoke(initial_state)

    assert final_state["resume_data"] == SAMPLE_RESUME
    assert final_state["jd_data"] == SAMPLE_JD


def test_graph_handles_llm_failure_gracefully(monkeypatch):
    """
    Agar LLM call fail ho (empty/garbage response), graph crash nahi hona chahiye,
    balki empty gap_analysis/questions ke saath aage badh jana chahiye.
    """
    mock_client = MockLLMClient(
        gap_response="not valid json {{{",
        questions_response="also not valid json [[[",
    )
    monkeypatch.setattr(interview_graph_module, "llm_client", mock_client)

    app_graph = build_graph()
    initial_state = get_initial_state(SAMPLE_RESUME, SAMPLE_JD)

    final_state = app_graph.invoke(initial_state)

    assert final_state["gap_analysis"] == {
        "strengths": [],
        "gaps": [],
        "partial_matches": [],
        "focus_areas": [],
    }
    assert final_state["questions"] == []
