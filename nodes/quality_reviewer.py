"""
Quality Reviewer Node.

Performs rule-based quality checks on final resume.
Validates length, ATS score, truthfulness, metric preservation, and wording quality.
"""

from typing import Dict, Any, List

from utils.constants import (
    MIN_QUALITY_RESUME_LENGTH,
    ATS_SCORE_THRESHOLD_GOOD,
)
from utils.logger import get_logger
from utils.metric_validator import validate_metric_preservation
from utils.ats_helper import calculate_ats_improvement

logger = get_logger(__name__)


def check_resume_length(final_resume: str) -> tuple[List[str], List[str]]:
    """
    Check if resume output is too short.
    """
    issues = []
    suggestions = []

    if len(final_resume.strip()) < MIN_QUALITY_RESUME_LENGTH:
        msg = f"Resume output seems too short (minimum {MIN_QUALITY_RESUME_LENGTH} characters)"
        issues.append(msg)
        suggestions.append("Add more verified projects, skills, or achievements.")
        logger.warning(f"Quality check: {msg}")

    return issues, suggestions


def check_ats_score(ats_score: float) -> tuple[List[str], List[str]]:
    """
    Check if official ATS score is below recommended threshold.
    """
    issues = []
    suggestions = []

    if ats_score < ATS_SCORE_THRESHOLD_GOOD:
        msg = f"ATS score is below recommended level ({ats_score}/100)"
        issues.append(msg)
        suggestions.append("Improve alignment with required skills from the job description.")
        logger.warning(f"Quality check: {msg}")

    return issues, suggestions


def check_hallucinations(hallucination_report: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """
    Check for potential hallucinations or fabricated content.
    """
    issues = []
    suggestions = []

    if not hallucination_report.get("is_truthful", False):
        msg = "Potential hallucination detected"
        issues.append(msg)
        suggestions.append("Remove unsupported claims before exporting.")
        logger.warning(f"Quality check: {msg}")

        report_issues = hallucination_report.get("issues", [])
        if report_issues:
            logger.debug(f"Hallucination report issues: {report_issues}")

    return issues, suggestions


def check_weak_phrases(final_resume: str) -> tuple[List[str], List[str]]:
    """
    Check for weak or generic resume phrases.
    """
    issues = []
    suggestions = []

    weak_phrases = [
        (
            "responsible for",
            "Replace 'responsible for' with stronger action verbs such as 'led', 'engineered', or 'developed'."
        ),
        (
            "robust",
            "Generic wording detected: replace 'robust' with specific technical details."
        ),
        (
            "worked on",
            "Replace 'worked on' with specific contribution verbs such as 'developed', 'optimized', or 'implemented'."
        ),
        (
            "helped with",
            "Replace 'helped with' with direct ownership language."
        ),
    ]

    resume_lower = final_resume.lower()

    for phrase, suggestion in weak_phrases:
        if phrase in resume_lower:
            msg = f"Weak phrase found: '{phrase}'"
            issues.append(msg)
            suggestions.append(suggestion)
            logger.warning(f"Quality check: {msg}")

    return issues, suggestions


def run_metric_preservation_check(
    original_resume_text: str,
    final_resume: str,
) -> Dict[str, Any]:
    """
    Validate whether important numeric metrics from the original resume
    are preserved in the rewritten resume.
    """
    try:
        return validate_metric_preservation(
            original_resume_text,
            final_resume
        )

    except Exception as e:
        logger.debug(f"Metric validator failed: {e}")
        return {
            "original_metrics": [],
            "preserved_metrics": [],
            "missing_metrics": [],
            "preservation_score": 0.0,
            "is_metric_safe": False,
        }


def run_ats_comparison(
    original_resume_text: str,
    final_resume: str,
    jd_analysis: Dict[str, Any],
    fallback_score: float,
) -> Dict[str, Any]:
    """
    Compare original resume and optimized resume using lightweight
    keyword coverage comparison.

    Note:
    This is not the official weighted ATS score.
    Official ATS score comes from ats_scorer_node.
    """
    try:
        return calculate_ats_improvement(
            original_resume_text=original_resume_text,
            final_resume_text=final_resume,
            jd_analysis=jd_analysis,
        )

    except Exception as e:
        logger.debug(f"ATS comparison calculation failed: {e}")
        return {
            "original_ats_score": fallback_score,
            "optimized_ats_score": fallback_score,
            "improvement": 0.0,
            "original_matched_terms": [],
            "optimized_matched_terms": [],
            "still_missing_terms": [],
        }


def quality_reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review final resume quality using rule-based checks.

    Checks:
    1. Resume length
    2. Official ATS score
    3. Hallucination report
    4. Weak phrases
    5. Metric preservation
    6. Keyword-based before/after comparison
    """
    logger.info("Starting quality reviewer node")

    try:
        final_resume = state.get("final_resume", "")
        raw_resume_text = state.get("raw_resume_text", "")
        ats_score = state.get("ats_score", 0)
        hallucination_report = state.get("hallucination_report", {})
        jd_analysis = state.get("jd_analysis", {})

        all_issues = []
        all_suggestions = []

        # 1. Length check
        length_issues, length_suggestions = check_resume_length(final_resume)
        all_issues.extend(length_issues)
        all_suggestions.extend(length_suggestions)

        # 2. Official ATS score check
        ats_issues, ats_suggestions = check_ats_score(ats_score)
        all_issues.extend(ats_issues)
        all_suggestions.extend(ats_suggestions)

        # 3. Hallucination check
        halluc_issues, halluc_suggestions = check_hallucinations(hallucination_report)
        all_issues.extend(halluc_issues)
        all_suggestions.extend(halluc_suggestions)

        # 4. Weak phrase check
        phrase_issues, phrase_suggestions = check_weak_phrases(final_resume)
        all_issues.extend(phrase_issues)
        all_suggestions.extend(phrase_suggestions)

        # 5. Metric preservation check
        metric_report = run_metric_preservation_check(
            original_resume_text=raw_resume_text,
            final_resume=final_resume,
        )

        if metric_report.get("missing_metrics"):
            missing_metrics = metric_report.get("missing_metrics", [])
            msg = f"Important metrics missing after rewrite: {', '.join(missing_metrics)}"
            all_issues.append(msg)
            all_suggestions.append("Ensure key numeric achievements are preserved in the final resume.")
            logger.warning(f"Quality check: {msg}")

        # 6. Keyword-based ATS before/after comparison
        ats_comparison = run_ats_comparison(
            original_resume_text=raw_resume_text,
            final_resume=final_resume,
            jd_analysis=jd_analysis,
            fallback_score=ats_score,
        )

        state["ats_comparison"] = ats_comparison

        # Final quality report
        if not all_issues:
            all_suggestions.append("Resume is structurally acceptable and ready for review.")
            logger.info("Quality check: Resume passed all checks")

        quality_report = {
            "ats_score": ats_score,
            "issues": all_issues,
            "suggestions": all_suggestions,
            "is_ready_for_export": len(all_issues) == 0,
            "metric_report": metric_report,
            "ats_comparison_note": (
                "ats_comparison is a lightweight keyword coverage comparison. "
                "Official ATS score is calculated by ats_scorer_node."
            ),
        }

        state["quality_report"] = quality_report

        status = "READY FOR EXPORT" if quality_report["is_ready_for_export"] else "HAS ISSUES"
        logger.info(f"Quality review completed: {status}")

    except Exception as e:
        logger.error(f"Quality reviewer node failed: {e}", exc_info=True)
        raise

    return state