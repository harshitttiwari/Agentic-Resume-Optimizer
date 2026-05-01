"""
Gap Analyzer Node.

Analyzes skill gaps between resume and job requirements.
Provides recommendations based on match level.
"""

import json
from typing import Dict, Any, List

from config import llm_strict
from prompts import MISSING_SKILL_SUGGESTION_PROMPT
from utils.error_handler import retry_on_rate_limit
from utils.constants import MATCH_LEVELS
from utils.logger import get_logger

logger = get_logger(__name__)


@retry_on_rate_limit(max_retries=2)
def suggest_missing_skill_bullets(
    missing_skills: List[str],
    parsed_resume: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    target_role: str,
) -> List[str]:
    if not missing_skills:
        return []

    prompt = MISSING_SKILL_SUGGESTION_PROMPT.format(
        target_role=target_role,
        missing_skills=json.dumps(missing_skills, indent=2, ensure_ascii=True),
        parsed_resume=json.dumps(parsed_resume, indent=2, ensure_ascii=True),
        jd_analysis=json.dumps(jd_analysis, indent=2, ensure_ascii=True),
    )

    try:
        judge = llm_strict()
        response = judge.invoke(prompt)
        payload = json.loads(response.content.strip())
        suggestions = payload.get("suggestions", [])
        return [str(item).strip() for item in suggestions if str(item).strip()]
    except Exception as exc:
        logger.debug("Suggestion generation failed: %s", exc)
        return [
            f"If applicable, add a bullet demonstrating {skill} experience."
            for skill in missing_skills
        ]


def get_match_level(ats_score: float) -> Dict[str, str]:
    """
    Classify resume match level based on ATS score.
    
    Args:
        ats_score: ATS score (0-100)
        
    Returns:
        Dictionary with classification and recommendations
    """
    for level_key in ["STRONG", "GOOD", "MODERATE", "WEAK"]:
        level_config = MATCH_LEVELS[level_key]
        if ats_score >= level_config["threshold"]:
            logger.info(f"Match level: {level_key} ({level_config['label']})")
            return level_config
    
    # Fallback to WEAK if no match
    return MATCH_LEVELS["WEAK"]


def gap_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze skill gaps and provide recommendations.
    
    Performs:
    1. Calculate match ratio
    2. Classify match level
    3. Generate recommendations
    4. Build gap report
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with gap_report
    """
    logger.info("Starting gap analyzer node")
    
    try:
        missing_skills = state.get("missing_skills", [])
        matched_skills = state.get("matched_skills", [])
        ats_score = state.get("ats_score", 0)
        parsed_resume = state.get("parsed_resume", {})
        jd_analysis = state.get("jd_analysis", {})
        target_role = state.get("target_role", "")
        
        matched_count = len(matched_skills)
        missing_count = len(missing_skills)
        total = matched_count + missing_count
        
        # Calculate match ratio
        match_ratio = matched_count / total if total else 0
        logger.debug(f"Match ratio: {match_ratio:.2%} ({matched_count}/{total})")
        
        # Get match level and recommendations
        match_level_info = get_match_level(ats_score)
        
        # Build gap report
        gap_report = {
            "ats_score": ats_score,
            "match_ratio": round(match_ratio, 2),
            "match_level": match_level_info["label"],
            "matched_skills_count": matched_count,
            "missing_skills_count": missing_count,
            "missing_skills": missing_skills,
            "recommendation": match_level_info["recommendation"],
        }
        
        state["gap_report"] = gap_report
        state["missing_skill_suggestions"] = suggest_missing_skill_bullets(
            missing_skills=missing_skills,
            parsed_resume=parsed_resume,
            jd_analysis=jd_analysis,
            target_role=target_role,
        )
        
        logger.info(
            f"Gap analysis completed: "
            f"{matched_count}/{total} skills matched, "
            f"recommendation: {match_level_info['label']}"
        )
        
    except Exception as e:
        logger.error(f"Gap analyzer node failed: {e}", exc_info=True)
        raise
    
    return state