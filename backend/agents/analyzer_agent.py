import json
from typing import Any, Dict

ANALYZER_SYSTEM_PROMPT = """You are an expert technical recruiter and interview coach.
You will be given a candidate's structured resume data and a structured job description.
Compare them carefully and identify:

1. strengths: skills/experience/projects from the resume that clearly match the JD
2. gaps: required skills or responsibilities from the JD that are NOT present in the resume
3. partial_matches: skills that are mentioned in the resume but depth/level is unclear
   compared to what the JD demands
4. focus_areas: 3-6 short phrases describing what an interviewer should probe deeply
   during the interview, based on the gaps and partial matches

Respond with ONLY valid JSON in exactly this shape, no extra text, no markdown fences:

{
  "strengths": ["..."],
  "gaps": ["..."],
  "partial_matches": ["..."],
  "focus_areas": ["..."]
}

If resume or JD data is empty/missing certain fields, do your best with what is available.
Never leave a key out of the JSON, even if its list is empty.
"""


def _json_safe_default(obj):
    """
    json.dumps ke liye fallback: agar koi field set/tuple jaisi non-JSON type ho,
    crash karne ki bajaye usse list mein convert kar do.
    """
    if isinstance(obj, (set, tuple, frozenset)):
        return list(obj)
    return str(obj)


def _build_prompt(resume_data: Dict[str, Any], jd_data: Dict[str, Any]) -> str:
    """
    GroqLLMClient.structure() ek hi prompt string leta hai (system + user alag nahi),
    isliye system instructions aur data ko ek combined prompt mein jodte hain.
    """
    return (
        f"{ANALYZER_SYSTEM_PROMPT}\n\n"
        "RESUME DATA (JSON):\n"
        f"{json.dumps(resume_data, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "JOB DESCRIPTION DATA (JSON):\n"
        f"{json.dumps(jd_data, ensure_ascii=False, default=_json_safe_default)}\n\n"
        "Compare them and return the gap analysis JSON as instructed."
    )


def _empty_gap_analysis() -> Dict[str, Any]:
    return {
        "strengths": [],
        "gaps": [],
        "partial_matches": [],
        "focus_areas": [],
    }


def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    LLM response ko JSON mein safely parse karta hai.
    Kabhi kabhi model ```json fences daal deta hai, unhe strip kar dete hain.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # agar "json" prefix laga ho to hata do
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return _empty_gap_analysis()

    result = _empty_gap_analysis()
    for key in result.keys():
        value = parsed.get(key, [])
        if isinstance(value, list):
            result[key] = value
        else:
            # agar model ne list ki jagah string ya kuch aur diya, list mein wrap kar do
            result[key] = [value] if value else []

    return result


def analyze_gap(
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    llm_client,
    model: str,
) -> Dict[str, Any]:
    """
    Resume aur JD ka structured data compare kar ke gap analysis nikalta hai.

    Args:
        resume_data: Day 1 ke resume parser se aaya structured dict
        jd_data: Day 1 ke JD parser se aaya structured dict
        llm_client: GroqLLMClient instance (ya test ke liye mock client) jispe
                    .structure(prompt, model) method ho
        model: Groq model name (config.Settings.GROQ_MODEL se aata hai)

    Returns:
        dict with keys: strengths, gaps, partial_matches, focus_areas
    """
    # Edge case: dono empty hain to LLM call karne ka faida nahi
    if not resume_data and not jd_data:
        return _empty_gap_analysis()

    resume_data = resume_data or {}
    jd_data = jd_data or {}

    prompt = _build_prompt(resume_data, jd_data)

    try:
        raw_response = llm_client.structure(prompt, model)
    except Exception:
        # LLM call fail ho jaye (network, API error, etc.) to safe empty result do
        return _empty_gap_analysis()

    return _parse_llm_json(raw_response)
