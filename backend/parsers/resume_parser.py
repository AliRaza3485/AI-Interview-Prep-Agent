"""
Resume Parser: PDF/DOCX -> raw text -> structured JSON.

Design decisions:
1. Text extraction and LLM structuring are SEPARATE functions.
   Extraction is deterministic (testable with a fake file, no API needed);
   structuring depends on an external API (testable with a mock LLM client).
2. structure_resume() takes an `llm_client` parameter instead of creating
   its own client internally -- dependency injection for testability.
3. The LLM prompt demands STRICT JSON with no markdown fences, and we still
   defensively strip fences before parsing, since LLMs sometimes add them anyway.
"""

import json
import re
from pathlib import Path
from typing import Protocol

import pdfplumber
from docx import Document


class ResumeParseError(Exception):
    """Raised when a resume file can't be read or produces no usable text."""


class LLMClient(Protocol):
    """Minimal interface any LLM client must satisfy (Groq, mock, etc.)."""

    def structure(self, prompt: str, model: str) -> str: ...


def extract_text(file_path: str) -> str:
    """
    Extract raw text from a PDF or DOCX resume.
    Raises ResumeParseError on corrupt files or unsupported formats.
    """
    path = Path(file_path)
    if not path.exists():
        raise ResumeParseError(f"File not found: {file_path}")

    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = "\n".join(text_parts)
        elif suffix == ".docx":
            doc = Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            raise ResumeParseError(
                f"Unsupported file type: {suffix}. Only .pdf and .docx are supported."
            )
    except ResumeParseError:
        raise
    except Exception as e:
        raise ResumeParseError(f"Failed to read {suffix} file: {e}") from e

    text = text.strip()
    if not text:
        raise ResumeParseError(
            "No extractable text found in resume (possibly a scanned image PDF "
            "with no text layer, or an empty document)."
        )
    return text


STRUCTURE_PROMPT = """You are a resume parsing engine. Extract structured data from the resume text below.

Return ONLY valid JSON, with no markdown code fences, no preamble, no explanation.
Use exactly this schema:

{{
  "skills": ["string", ...],
  "experience": [
    {{"title": "string", "company": "string", "duration": "string", "highlights": ["string", ...]}}
  ],
  "projects": [
    {{"name": "string", "description": "string", "tech_stack": ["string", ...]}}
  ],
  "education": [
    {{"degree": "string", "institution": "string", "year": "string"}}
  ]
}}

If a section is missing from the resume, return an empty list for it. Do not invent data.

RESUME TEXT:
---
{resume_text}
---
"""


def _strip_json_fences(text: str) -> str:
    """Defensively strip ```json ... ``` fences if the LLM adds them anyway."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return cleaned.strip()


def structure_resume(raw_text: str, llm_client: LLMClient, model: str) -> dict:
    """
    Turn raw resume text into structured JSON using an injected LLM client.
    """
    prompt = STRUCTURE_PROMPT.format(resume_text=raw_text)
    response_text = llm_client.structure(prompt, model)
    cleaned = _strip_json_fences(response_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ResumeParseError(
            f"LLM returned invalid JSON for resume structuring: {e}\nRaw response: {cleaned[:300]}"
        ) from e

    for key in ("skills", "experience", "projects", "education"):
        data.setdefault(key, [])

    return data
