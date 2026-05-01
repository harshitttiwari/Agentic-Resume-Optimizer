"""
Simple metric extraction and preservation validator.

Functions:
- extract_metrics(text: str) -> list[str]
- validate_metric_preservation(original_text: str, rewritten_text: str) -> dict
"""

import re
from typing import List, Dict, Set


_PATTERNS = [
    # CGPA / GPA: CGPA: 8.34, GPA 3.8/4.0
    r"\b(?:CGPA|GPA)[:\s]*\d(?:\.\d+)?(?:/\d(?:\.\d+)?)?\b",

    # Grade / score percentages: Grade: 84.6%, Score 95%
    r"\b(?:Grade|Score|Marks)[:\s]*\d{1,3}(?:\.\d+)?\s*%\+?\b",

    # Percentages like 40%, 82.3%, 80%+
    r"\b\d{1,3}(?:\.\d+)?\s*%\+?",

    # Numbers with trailing plus: 50+, 100+
    r"\b\d{1,6}\+\b",

    # Token counts: 500-token, 500 token, 500 tokens
    r"\b\d+[-\s]?tokens?\b",

    # Latency: sub-100 ms, 120 ms, 1.5 sec
    r"\bsub[-\s]?\d+\s*ms\b",
    r"\b\d+(?:\.\d+)?\s*(?:ms|sec|seconds|milliseconds)\b",

    # Durations: 2 years, 6 months, 3 weeks
    r"\b\d+\s*(?:years|year|yrs|months|month|weeks|week|days|day)\b",

    # Years and date ranges
    r"\b\d{4}(?:[-/]\d{2,4})?\b",
]


def _find_all_unique(patterns: List[str], text: str) -> List[str]:
    found: List[str] = []
    seen: Set[str] = set()

    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            token = str(match).strip()
            key = _normalize_metric(token)

            if token and key not in seen:
                seen.add(key)
                found.append(token)

    return found


def extract_metrics(text: str) -> List[str]:
    """Extract likely metric tokens from free text."""
    if not text:
        return []

    metrics = _find_all_unique(_PATTERNS, text)

    cleaned = []

    for metric in metrics:
        metric = re.sub(r"\s+", " ", metric).strip()

        if 1 < len(metric) < 100:
            cleaned.append(metric)

    return cleaned


def _normalize_metric(metric: str) -> str:
    """
    Normalize metric for strict comparison.

    Keeps important context like CGPA, Grade, token, ms, %, etc.
    """
    metric = str(metric).lower().strip()
    metric = re.sub(r"\s+", "", metric)
    metric = metric.replace("-", "-").replace("–", "-").replace("—", "-")
    metric = re.sub(r"^[^0-9a-z]+|[^0-9a-z%+:/.-]+$", "", metric)
    return metric


def _is_preserved(original_metric: str, rewritten_metrics: List[str]) -> bool:
    """
    Check whether an original metric is preserved.

    Uses normalized exact matching.
    Allows minor hyphen/space variations like:
    500-token == 500 token
    sub-100 ms == sub 100 ms
    """
    original_norm = _normalize_metric(original_metric)

    rewritten_norms = {_normalize_metric(metric) for metric in rewritten_metrics}

    if original_norm in rewritten_norms:
        return True

    # Hyphen/space tolerant comparison
    original_loose = original_norm.replace("-", "")

    for rewritten_norm in rewritten_norms:
        rewritten_loose = rewritten_norm.replace("-", "")

        if original_loose == rewritten_loose:
            return True

    return False


def validate_metric_preservation(original_text: str, rewritten_text: str) -> Dict:
    """
    Compare metrics found in original and rewritten resume.

    Returns:
    {
      "original_metrics": [],
      "preserved_metrics": [],
      "missing_metrics": [],
      "preservation_score": 0.0,
      "is_metric_safe": bool
    }
    """
    original_metrics = extract_metrics(original_text or "")
    rewritten_metrics = extract_metrics(rewritten_text or "")

    preserved = []
    missing = []

    for metric in original_metrics:
        if _is_preserved(metric, rewritten_metrics):
            preserved.append(metric)
        else:
            missing.append(metric)

    total = len(original_metrics)
    score = len(preserved) / total if total else 1.0

    return {
        "original_metrics": original_metrics,
        "preserved_metrics": preserved,
        "missing_metrics": missing,
        "preservation_score": round(score, 3),
        "is_metric_safe": score >= 0.8,
    }