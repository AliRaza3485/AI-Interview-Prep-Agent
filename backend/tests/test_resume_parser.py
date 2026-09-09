import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.resume_parser import extract_text, structure_resume, ResumeParseError

RESUME_PATH = str(
    Path(__file__).parent.parent.parent
    / "data"
    / "sample_resumes"
    / "updated resume.pdf"
)


class MockLLMClient:
    """Fake LLM client -- returns a canned response, no real API call."""

    def __init__(self, response_text: str):
        self.response_text = response_text

    def structure(self, prompt: str, model: str) -> str:
        return self.response_text


def test_extract_text_from_real_resume():
    text = extract_text(RESUME_PATH)
    assert len(text) > 0
    print("\nExtracted text preview:\n", text[:300])


def test_structure_resume_with_mock():
    fake_json = '{"skills": ["Python", "FastAPI"], "experience": [], "projects": [], "education": []}'
    mock_client = MockLLMClient(fake_json)

    result = structure_resume(
        "dummy raw text", mock_client, model="llama-3.3-70b-versatile"
    )

    assert result["skills"] == ["Python", "FastAPI"]
    assert result["experience"] == []


def test_extract_text_from_docx_resume():
    docx_path = str(
        Path(__file__).parent.parent.parent
        / "data"
        / "sample_resumes"
        / "updated resume.docx"
    )
    text = extract_text(docx_path)
    assert len(text) > 0
    print("\nDOCX extracted text preview:\n", text[:300])
