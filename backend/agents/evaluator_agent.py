import json
from typing import Any, Dict

EVALUATOR_SYSTEM_PROMPT = """You are an expert technical interviewer evaluating a
candidate's answer to an interview question. You will be given:
1. The interview question that was asked (with its category, difficulty, and target)
2. The candidate's answer to that question
3. The job description context (role, required skills, responsibilities)

Evaluate the answer fairly and constructively. Consider:
- Technical accuracy and depth (for technical/project_deep_dive questions)
- Clarity of communication and structure
- Relevance to what the question actually asked
- Whether the answer demonstrates the skill/experience the question was targeting

Respond with ONLY valid JSON in exactly this shape, no extra text, no markdown fences:

{
  "score": <integer from 0 to 10>,
  "feedback": "<2-3 sentence overall assessment>",
  "strengths_shown": ["<short phrase>", ...],
  "improvement_areas": ["<short phrase>", ...]
}

If the answer is empty, off-topic, or says "I don't know", give a low score (0-2) and
explain why in the feedback, but still return valid JSON with all keys present.
"""


def _build_prompt(
    question: Dict[str, Any],
    answer: str,
    jd_data: Dict[str, Any],
) -> str:
    return (
        f"{EVALUATOR_SYSTEM_PROMPT}\n\n"
        "QUESTION (JSON):\n"
        f"{json.dumps(question, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "CANDIDATE'S ANSWER:\n"
        f"{answer}\n\n"
        "JOB DESCRIPTION CONTEXT (JSON):\n"
        f"{json.dumps(jd_data, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "Evaluate this answer and return the evaluation JSON as instructed."
    )


def _json_safe_default(obj):
    """
    json.dumps ke liye fallback: agar koi field set/tuple jaisi non-JSON type ho,
    crash karne ki bajaye usse list mein convert kar do.
    """
    if isinstance(obj, (set, tuple, frozenset)):
        return list(obj)
    return str(obj)


def _empty_evaluation() -> Dict[str, Any]:
    return {
        "score": 0,
        "feedback": "Could not evaluate this answer due to a technical issue.",
        "strengths_shown": [],
        "improvement_areas": [],
    }


def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    LLM response ko JSON mein safely parse karta hai, aur fields ko validate karta hai.
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
        return _empty_evaluation()

    if not isinstance(parsed, dict):
        return _empty_evaluation()

    result = _empty_evaluation()

    # score: must be an int between 0-10, otherwise fallback to 0
    score = parsed.get("score", 0)
    if isinstance(score, (int, float)):
        result["score"] = max(0, min(10, int(score)))

    # feedback: must be a string
    feedback = parsed.get("feedback", "")
    if isinstance(feedback, str) and feedback.strip():
        result["feedback"] = feedback

    # strengths_shown / improvement_areas: must be lists
    for key in ("strengths_shown", "improvement_areas"):
        value = parsed.get(key, [])
        if isinstance(value, list):
            result[key] = value

    return result


def evaluate_answer(
    question: Dict[str, Any],
    answer: str,
    jd_data: Dict[str, Any],
    llm_client,
    model: str,
) -> Dict[str, Any]:
    """
    Ek question aur uska candidate answer leke evaluate karta hai.

    Args:
        question: questions list ka ek item, jaisa {question, category, difficulty, targets}
        answer: candidate ka diya hua jawab (plain text)
        jd_data: Day 1 ke JD parser se aaya structured dict (context ke liye)
        llm_client: GroqLLMClient instance (ya mock) jispe .structure(prompt, model) ho
        model: Groq model name (config.Settings.GROQ_MODEL se)

    Returns:
        dict with keys: score, feedback, strengths_shown, improvement_areas
    """
    # Edge case: khali answer ho to LLM call ki zaroorat nahi, seedha low score
    if not answer or not answer.strip():
        return {
            "score": 0,
            "feedback": "No answer was provided.",
            "strengths_shown": [],
            "improvement_areas": ["Attempt to answer every question, even partially."],
        }

    question = question or {}
    jd_data = jd_data or {}

    prompt = _build_prompt(question, answer, jd_data)

    try:
        raw_response = llm_client.structure(prompt, model)
    except Exception:
        return _empty_evaluation()

    return _parse_llm_json(raw_response)
