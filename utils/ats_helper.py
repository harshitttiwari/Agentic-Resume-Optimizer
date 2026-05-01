"""
Helper for ATS before/after comparison.

This module estimates how much the optimized resume improved
against the job description using simple but explainable matching.
"""

from typing import Dict, Any, List
import re


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return str(text).lower().strip()


def extract_all_jd_terms(jd_analysis: Dict[str, Any]) -> List[str]:
    """Collect all relevant JD terms into one deduplicated list."""
    terms = []

    for key in ["required_skills", "preferred_skills", "tools", "keywords"]:
        terms.extend(jd_analysis.get(key, []))

    cleaned = []
    seen = set()

    for term in terms:
        term = str(term).strip()
        key = term.lower()

        if term and key not in seen:
            cleaned.append(term)
            seen.add(key)

    return cleaned


def text_contains_term(text: str, term: str) -> bool:
    """Check if a JD term appears in resume text."""
    text = normalize_text(text)
    term = normalize_text(term)

    if not term or len(term) < 2:
        return False

    escaped = re.escape(term)

    if len(term.split()) == 1:
        pattern = r"\b" + escaped + r"\b"
    else:
        pattern = escaped

    return bool(re.search(pattern, text))


def calculate_resume_ats_score(
    resume_text: str,
    jd_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate a simple explainable ATS score for any resume text.

    Used for before/after comparison.
    """

    jd_terms = extract_all_jd_terms(jd_analysis)

    if not resume_text or not jd_terms:
        return {
            "score": 0.0,
            "matched_terms": [],
            "missing_terms": jd_terms,
            "total_terms": len(jd_terms),
        }

    matched_terms = []
    missing_terms = []

    for term in jd_terms:
        if text_contains_term(resume_text, term):
            matched_terms.append(term)
        else:
            missing_terms.append(term)

    score = (len(matched_terms) / len(jd_terms)) * 100
    score = round(score, 2)

    return {
        "score": score,
        "matched_terms": matched_terms,
        "missing_terms": missing_terms,
        "total_terms": len(jd_terms),
    }


def calculate_ats_improvement(
    original_resume_text: str,
    final_resume_text: str,
    jd_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare ATS score before and after resume rewriting.
    """

    original = calculate_resume_ats_score(
        resume_text=original_resume_text,
        jd_analysis=jd_analysis,
    )

    optimized = calculate_resume_ats_score(
        resume_text=final_resume_text,
        jd_analysis=jd_analysis,
    )

    improvement = round(optimized["score"] - original["score"], 2)

    return {
        "original_ats_score": original["score"],
        "optimized_ats_score": optimized["score"],
        "improvement": improvement,
        "original_matched_terms": original["matched_terms"],
        "optimized_matched_terms": optimized["matched_terms"],
        "still_missing_terms": optimized["missing_terms"],
    }