import json
from typing import Any, Dict, List, Tuple

DIFFICULTY_WEIGHTS = {"easy": 1, "medium": 2, "hard": 3}

GAP_ADDRESSED_SCORE_THRESHOLD = 6  # is score ya zyada = gap "addressed" mana jayega

READINESS_THRESHOLDS = [
    (8.0, "Ready for Real Interviews"),
    (5.0, "Almost Ready"),
]
DEFAULT_READINESS = "Needs More Practice"


def _json_safe_default(obj):
    if isinstance(obj, (set, tuple, frozenset)):
        return list(obj)
    return str(obj)


# ---------- Pure calculation functions (no LLM) ----------


def _compute_overall_score(
    questions: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]
) -> float:
    """
    Difficulty-weighted average score nikalta hai.
    Hard questions ka zyada weight hota hai easy questions ke muqable.
    """
    if not questions or not evaluations:
        return 0.0

    total_weighted_score = 0.0
    total_weight = 0.0

    for question, evaluation in zip(questions, evaluations):
        difficulty = question.get("difficulty", "medium")
        weight = DIFFICULTY_WEIGHTS.get(difficulty, 2)
        score = evaluation.get("score", 0)

        total_weighted_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(total_weighted_score / total_weight, 1)


def _compute_readiness_level(overall_score: float) -> str:
    for threshold, label in READINESS_THRESHOLDS:
        if overall_score >= threshold:
            return label
    return DEFAULT_READINESS


def _compute_category_breakdown(
    questions: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Har category (technical/behavioral/project_deep_dive) ka average score
    aur kitne questions the, yeh nikalta hai.
    """
    buckets: Dict[str, List[int]] = {}

    for question, evaluation in zip(questions, evaluations):
        category = question.get("category", "unknown")
        score = evaluation.get("score", 0)
        buckets.setdefault(category, []).append(score)

    breakdown = {}
    for category, scores in buckets.items():
        breakdown[category] = {
            "average_score": round(sum(scores) / len(scores), 1),
            "questions_count": len(scores),
        }

    return breakdown


def _match_gaps(
    gap_analysis: Dict[str, Any],
    questions: List[Dict[str, Any]],
    evaluations: List[Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """
    gap_analysis ke 'gaps' ko questions ke 'targets' field se match karta hai
    (simple case-insensitive substring match), aur dekhta hai us gap se related
    question(s) ka average score threshold se upar hai ya nahi.

    Returns:
        (gaps_addressed, gaps_still_open)
    """
    gaps = gap_analysis.get("gaps", [])
    if not gaps:
        return [], []

    gaps_addressed = []
    gaps_still_open = []

    for gap in gaps:
        gap_lower = str(gap).lower()
        matched_scores = []

        for question, evaluation in zip(questions, evaluations):
            target = str(question.get("targets", "")).lower()
            if gap_lower in target or target in gap_lower:
                matched_scores.append(evaluation.get("score", 0))

        if not matched_scores:
            # Gap ko koi question hi test nahi karta - abhi bhi open hai
            gaps_still_open.append(gap)
            continue

        avg_score = sum(matched_scores) / len(matched_scores)
        if avg_score >= GAP_ADDRESSED_SCORE_THRESHOLD:
            gaps_addressed.append(gap)
        else:
            gaps_still_open.append(gap)

    return gaps_addressed, gaps_still_open


def _aggregate_raw_feedback(
    evaluations: List[Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """
    Har evaluation ke strengths_shown/improvement_areas ko ek list mein
    collect karta hai, duplicates hata deta hai. Yeh LLM ko polish karne
    ke liye raw material dega.
    """
    raw_strengths = []
    raw_weaknesses = []

    for evaluation in evaluations:
        for item in evaluation.get("strengths_shown", []):
            if item not in raw_strengths:
                raw_strengths.append(item)
        for item in evaluation.get("improvement_areas", []):
            if item not in raw_weaknesses:
                raw_weaknesses.append(item)

    return raw_strengths, raw_weaknesses


def _build_question_breakdown(
    questions: List[Dict[str, Any]],
    answers: List[str],
    evaluations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Deterministic pass-through: har question/answer/evaluation ko ek row mein
    combine karta hai. LLM isse regenerate nahi karta, seedha data se banta hai.
    """
    breakdown = []
    for i, question in enumerate(questions):
        answer = answers[i] if i < len(answers) else ""
        evaluation = evaluations[i] if i < len(evaluations) else {}
        breakdown.append(
            {
                "question": question.get("question", ""),
                "category": question.get("category", ""),
                "difficulty": question.get("difficulty", ""),
                "answer": answer,
                "score": evaluation.get("score", 0),
                "feedback": evaluation.get("feedback", ""),
            }
        )
    return breakdown


# ---------- LLM-based narrative synthesis ----------

REPORT_NARRATIVE_SYSTEM_PROMPT = """You are an expert interview coach writing the
narrative portion of a mock-interview practice report for a candidate.

You will be given:
1. A raw list of strengths observed across the candidate's answers
2. A raw list of improvement areas observed across the candidate's answers
3. Overall score and category breakdown (for context only)
4. Which job-requirement gaps were addressed and which are still open

Your job is ONLY to:
- Pick the 3-5 most important, non-redundant strengths (rewrite them clearly)
- Pick the 3-5 most important, non-redundant improvement areas (rewrite them clearly)
- Write a short (3-5 sentence) recommendation_summary: what the candidate should
  focus on before a real interview, written directly to the candidate, encouraging
  but honest. Do NOT claim to predict whether they will be hired.

Respond with ONLY valid JSON in exactly this shape, no extra text, no markdown fences:

{
  "key_strengths": ["...", ...],
  "key_weaknesses": ["...", ...],
  "recommendation_summary": "..."
}
"""


def _build_narrative_prompt(
    raw_strengths: List[str],
    raw_weaknesses: List[str],
    overall_score: float,
    category_breakdown: Dict[str, Any],
    gaps_addressed: List[str],
    gaps_still_open: List[str],
) -> str:
    return (
        f"{REPORT_NARRATIVE_SYSTEM_PROMPT}\n\n"
        f"RAW STRENGTHS OBSERVED:\n{json.dumps(raw_strengths, default=_json_safe_default)}\n\n"
        f"RAW IMPROVEMENT AREAS OBSERVED:\n{json.dumps(raw_weaknesses, default=_json_safe_default)}\n\n"
        f"OVERALL SCORE (0-10): {overall_score}\n\n"
        f"CATEGORY BREAKDOWN:\n{json.dumps(category_breakdown, default=_json_safe_default)}\n\n"
        f"GAPS ADDRESSED WELL:\n{json.dumps(gaps_addressed, default=_json_safe_default)}\n\n"
        f"GAPS STILL OPEN:\n{json.dumps(gaps_still_open, default=_json_safe_default)}\n\n"
        "Now write the JSON as instructed."
    )


def _empty_narrative() -> Dict[str, Any]:
    return {
        "key_strengths": [],
        "key_weaknesses": [],
        "recommendation_summary": "Could not generate a summary due to a technical issue.",
    }


def _parse_narrative_json(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return _empty_narrative()

    if not isinstance(parsed, dict):
        return _empty_narrative()

    result = _empty_narrative()

    for key in ("key_strengths", "key_weaknesses"):
        value = parsed.get(key, [])
        if isinstance(value, list):
            result[key] = value

    summary = parsed.get("recommendation_summary", "")
    if isinstance(summary, str) and summary.strip():
        result["recommendation_summary"] = summary

    return result


# ---------- Main entry point ----------


def generate_report(
    questions: List[Dict[str, Any]],
    answers: List[str],
    evaluations: List[Dict[str, Any]],
    gap_analysis: Dict[str, Any],
    llm_client,
    model: str,
) -> Dict[str, Any]:
    """
    Poore interview session (questions, answers, evaluations, gap_analysis) se
    ek final report banata hai. Numbers/matching code se, narrative LLM se.
    """
    overall_score = _compute_overall_score(questions, evaluations)
    readiness_level = _compute_readiness_level(overall_score)
    category_breakdown = _compute_category_breakdown(questions, evaluations)
    gaps_addressed, gaps_still_open = _match_gaps(gap_analysis, questions, evaluations)
    question_breakdown = _build_question_breakdown(questions, answers, evaluations)
    raw_strengths, raw_weaknesses = _aggregate_raw_feedback(evaluations)

    # Agar koi evaluation hi nahi hui (interview incomplete), LLM call ka faida nahi
    if not evaluations:
        narrative = _empty_narrative()
    else:
        prompt = _build_narrative_prompt(
            raw_strengths,
            raw_weaknesses,
            overall_score,
            category_breakdown,
            gaps_addressed,
            gaps_still_open,
        )
        try:
            raw_response = llm_client.structure(prompt, model)
            narrative = _parse_narrative_json(raw_response)
        except Exception:
            narrative = _empty_narrative()

    return {
        "overall_score": overall_score,
        "readiness_level": readiness_level,
        "category_breakdown": category_breakdown,
        "gaps_addressed": gaps_addressed,
        "gaps_still_open": gaps_still_open,
        "key_strengths": narrative["key_strengths"],
        "key_weaknesses": narrative["key_weaknesses"],
        "recommendation_summary": narrative["recommendation_summary"],
        "question_breakdown": question_breakdown,
    }
