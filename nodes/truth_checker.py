"""
Truth Checker Node.

Checks whether the rewritten resume contains fabricated content.
Also removes only obvious false positives when the flagged term already exists
clearly in the original resume.
"""

from typing import Dict, Any
import json
import re

from config import llm_strict
from prompts import TRUTH_CHECKER_PROMPT
from utils.logger import get_logger
from utils.error_handler import retry_on_rate_limit

logger = get_logger(__name__)


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """Safely extract JSON from LLM response."""
    response_text = response_text.strip()

    response_text = re.sub(r"```json", "", response_text, flags=re.IGNORECASE)
    response_text = re.sub(r"```", "", response_text)
    response_text = response_text.strip()

    start = response_text.find("{")
    end = response_text.rfind("}") + 1

    if start == -1 or end == 0:
        return {
            "is_truthful": False,
            "issues": ["Truth checker did not return valid JSON."]
        }

    json_text = response_text[start:end]

    try:
        return json.loads(json_text)
    except Exception:
        return {
            "is_truthful": False,
            "issues": ["Truth checker JSON parsing failed."]
        }


def normalize_text(text: str) -> str:
    """Normalize text for safer comparison."""
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def clean_false_positive_issues(report: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """
    Remove only clear false positives.

    Important:
    Do not remove an issue just because one quoted word exists.
    Remove only when the exact fabricated phrase already exists in the original resume.
    """
    original_lower = normalize_text(original_text)
    cleaned_issues = []

    for issue in report.get("issues", []):
        issue_text = normalize_text(issue)

        # Known false-positive cleanup
        if "hugging face spaces" in issue_text and "hugging face spaces" in original_lower:
            continue

        # Safer generic cleanup:
        # If LLM explicitly says quoted term is fabricated, remove only if that exact quoted term exists.
        quoted_terms = re.findall(r'"([^"]+)"', str(issue))

        should_remove = False
        for term in quoted_terms:
            term_lower = normalize_text(term)

            if len(term_lower) >= 4 and term_lower in original_lower:
                should_remove = True
                break

        if should_remove:
            continue

        cleaned_issues.append(issue)

    report["issues"] = cleaned_issues
    report["is_truthful"] = len(cleaned_issues) == 0

    return report


@retry_on_rate_limit(max_retries=2)
def call_truth_checker_llm(prompt: str):
    """Call strict LLM for truth checking."""
    llm = llm_strict()
    return llm.invoke(prompt)


def truth_checker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Check whether rewritten resume contains fabricated content."""
    logger.info("Starting truth checker node")

    try:
        parsed_resume = state.get("parsed_resume", {})
        rewritten_resume = state.get("rewritten_resume") or state.get("final_resume", "")
        raw_resume_text = state.get("raw_resume_text", "")

        prompt = TRUTH_CHECKER_PROMPT.format(
            parsed_resume=json.dumps(parsed_resume, ensure_ascii=False, indent=2),
            rewritten_resume=rewritten_resume
        )

        response = call_truth_checker_llm(prompt)
        report = extract_json_from_response(response.content)

        report = clean_false_positive_issues(
            report=report,
            original_text=raw_resume_text
        )

        state["hallucination_report"] = report

        status = "TRUTHFUL" if report.get("is_truthful", False) else "NOT TRUTHFUL"
        logger.info(f"Truth check completed: {status}")

    except Exception as e:
        logger.error(f"Truth checker node failed: {e}", exc_info=True)

        state["hallucination_report"] = {
            "is_truthful": False,
            "issues": [f"Truth checker failed: {str(e)}"]
        }

    return state