import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.jd_parser import structure_jd, JDParseError


class MockLLMClient:
    """Fake LLM client -- returns a canned response, no real API call."""

    def __init__(self, response_text: str):
        self.response_text = response_text

    def structure(self, prompt: str, model: str) -> str:
        return self.response_text


def test_structure_jd_with_mock():
    fake_json = """{
        "role_title": "AI/ML Engineer",
        "role_level": "Mid",
        "required_skills": ["Python", "LangChain", "RAG"],
        "nice_to_have_skills": ["AWS"],
        "responsibilities": ["Build and maintain RAG pipelines"],
        "keywords": ["RAG", "LangGraph"]
    }"""
    mock_client = MockLLMClient(fake_json)

    result = structure_jd(
        "We are hiring an AI/ML engineer...",
        mock_client,
        model="llama-3.3-70b-versatile",
    )

    assert result["role_title"] == "AI/ML Engineer"
    assert "RAG" in result["required_skills"]


def test_structure_jd_empty_text_raises():
    mock_client = MockLLMClient("{}")
    try:
        structure_jd("   ", mock_client, model="llama-3.3-70b-versatile")
        assert False, "Expected JDParseError but no exception was raised"
    except JDParseError:
        pass


def test_structure_jd_missing_keys_default_to_empty():
    fake_json = '{"role_title": "AI Engineer"}'
    mock_client = MockLLMClient(fake_json)

    result = structure_jd("some jd text", mock_client, model="llama-3.3-70b-versatile")

    assert result["role_title"] == "AI Engineer"
    assert result["required_skills"] == []
    assert result["keywords"] == []
