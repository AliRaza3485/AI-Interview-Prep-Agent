"""
Job Description Parser: raw JD text -> structured JSON.

Note: JD input is usually pasted text (not a file), so there's no
extract_text() step here like resume_parser -- just structuring.
"""

import json
import re
from typing import Protocol


class JDParseError(Exception):
    """Raised when JD text is unusable or the LLM fails to structure it."""


class LLMClient(Protocol):
    def structure(self, prompt: str, model: str) -> str: ...


STRUCTURE_PROMPT = """You are a job description parsing engine. Extract structured data from the job description below.

Return ONLY valid JSON, with no markdown code fences, no preamble, no explanation.
Use exactly this schema:

{{
  "role_title": "string",
  "role_level": "string (e.g. Junior, Mid, Senior, Lead)",
  "required_skills": ["string", ...],
  "nice_to_have_skills": ["string", ...],
  "responsibilities": ["string", ...],
  "keywords": ["string", ...]
}}

"keywords" should capture domain/technology terms useful for tailoring interview questions
(e.g. "RAG", "LangGraph", "AWS"), not generic words.
If a section is missing or unclear, return an empty list/string for it. Do not invent data.

JOB DESCRIPTION TEXT:
---
{jd_text}
---
"""


def _strip_json_fences(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return cleaned.strip()


def structure_jd(jd_text: str, llm_client: LLMClient, model: str) -> dict:
    jd_text = jd_text.strip()
    if not jd_text:
        raise JDParseError("Job description text is empty.")

    prompt = STRUCTURE_PROMPT.format(jd_text=jd_text)
    response_text = llm_client.structure(prompt, model)
    cleaned = _strip_json_fences(response_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise JDParseError(
            f"LLM returned invalid JSON for JD structuring: {e}\nRaw response: {cleaned[:300]}"
        ) from e

    data.setdefault("role_title", "")
    data.setdefault("role_level", "")
    for key in (
        "required_skills",
        "nice_to_have_skills",
        "responsibilities",
        "keywords",
    ):
        data.setdefault(key, [])

    return data
