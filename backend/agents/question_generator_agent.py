import json
from typing import Any, Dict, List

DEFAULT_QUESTION_COUNT = 8

QUESTION_GENERATOR_SYSTEM_PROMPT = """You are an expert technical interviewer preparing
a mock interview for a candidate. You will be given:
1. A gap analysis (strengths, gaps, partial_matches, focus_areas)
2. The candidate's resume data (skills, experience, projects, education)
3. The job description data (role, required skills, responsibilities)

Generate a list of interview questions that:
- Prioritize the "gaps" and "focus_areas" from the gap analysis (test what's weak/unclear)
- Include at least 1-2 "project_deep_dive" questions based on the candidate's actual
  projects/experience from the resume
- Include a mix of categories: technical, behavioral, project_deep_dive
- Include a mix of difficulty: easy, medium, hard
- Each question should be specific to this candidate and this job, not generic

Generate exactly {question_count} questions.

Respond with ONLY valid JSON: a list of objects, no extra text, no markdown fences.
Each object must look exactly like this:

{{
  "question": "the actual interview question text",
  "category": "technical" | "behavioral" | "project_deep_dive",
  "difficulty": "easy" | "medium" | "hard",
  "targets": "short phrase describing which skill/gap/project this question tests"
}}

Return a JSON array of {question_count} such objects, nothing else.
"""


def _json_safe_default(obj):
    """
    json.dumps ke liye fallback: agar koi field set/tuple jaisi non-JSON type ho,
    crash karne ki bajaye usse list mein convert kar do.
    """
    if isinstance(obj, (set, tuple, frozenset)):
        return list(obj)
    return str(obj)


def _build_prompt(
    gap_analysis: Dict[str, Any],
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    question_count: int,
) -> str:
    system_part = QUESTION_GENERATOR_SYSTEM_PROMPT.format(question_count=question_count)
    return (
        f"{system_part}\n\n"
        "GAP ANALYSIS (JSON):\n"
        f"{json.dumps(gap_analysis, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "RESUME DATA (JSON):\n"
        f"{json.dumps(resume_data, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "JOB DESCRIPTION DATA (JSON):\n"
        f"{json.dumps(jd_data, ensure_ascii=False, default=_json_safe_default)}\n\n"
        f"Now generate exactly {question_count} tailored interview questions as instructed."
    )


VALID_CATEGORIES = {"technical", "behavioral", "project_deep_dive"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def _parse_llm_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    LLM response ko JSON list mein safely parse karta hai.
    Markdown fences strip karta hai, aur har question object ko validate karta hai.
    Invalid/malformed entries ko silently skip kar deta hai.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return []

    if not isinstance(parsed, list):
        return []

    valid_questions = []
    for item in parsed:
        if not isinstance(item, dict):
            continue

        question_text = item.get("question")
        category = item.get("category")
        difficulty = item.get("difficulty")
        targets = item.get("targets", "")

        if not question_text or not isinstance(question_text, str):
            continue
        if category not in VALID_CATEGORIES:
            continue
        if difficulty not in VALID_DIFFICULTIES:
            continue

        valid_questions.append(
            {
                "question": question_text,
                "category": category,
                "difficulty": difficulty,
                "targets": targets if isinstance(targets, str) else "",
            }
        )

    return valid_questions


def generate_questions(
    gap_analysis: Dict[str, Any],
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    llm_client,
    model: str,
    question_count: int = DEFAULT_QUESTION_COUNT,
) -> List[Dict[str, Any]]:
    """
    Gap analysis + resume + JD ke hisaab se tailored interview questions banata hai.

    Args:
        gap_analysis: analyze_gap() ka output (strengths, gaps, partial_matches, focus_areas)
        resume_data: Day 1 ke resume parser se aaya structured dict
        jd_data: Day 1 ke JD parser se aaya structured dict
        llm_client: GroqLLMClient instance (ya mock) jispe .structure(prompt, model) ho
        model: Groq model name (config.Settings.GROQ_MODEL se)
        question_count: kitne questions generate karne hain (default 8)

    Returns:
        list of dicts, har dict mein: question, category, difficulty, targets
    """
    # Edge case: agar teeno inputs hi khali hain, LLM call ka faida nahi
    if not gap_analysis and not resume_data and not jd_data:
        return []

    gap_analysis = gap_analysis or {}
    resume_data = resume_data or {}
    jd_data = jd_data or {}

    prompt = _build_prompt(gap_analysis, resume_data, jd_data, question_count)

    try:
        raw_response = llm_client.structure(prompt, model)
    except Exception:
        return []

    return _parse_llm_json(raw_response)
