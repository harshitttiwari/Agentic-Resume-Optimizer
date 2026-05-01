"""
ATS Scorer Node.

Calculates ATS compatibility score based on skill matching and evidence.
Provides detailed breakdown of scoring components.
"""

from typing import Dict, Any, List
from utils.constants import (
    ATS_SKILL_COVERAGE_WEIGHT,
    ATS_REQUIRED_WEIGHT,
    ATS_EVIDENCE_WEIGHT,
    ATS_MISSING_SKILL_PENALTY,
    ATS_MAX_PENALTY
)
from utils.logger import get_logger

logger = get_logger(__name__)


def normalize_skill(skill: str) -> str:
    """Normalize skill for comparison."""
    return str(skill).lower().strip()


def ats_scorer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate ATS score based on skill matching and evidence.
    
    Scoring formula:
    - Skill Coverage (60%): Ratio of matched to total skills
    - Required Skills (25%): Coverage of required skills only
    - Evidence Confidence (15%): Average confidence of matched skills
    - Missing Penalty: -2 points per missing required skill (max -12)
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with ats_score and ats_breakdown
    """
    logger.info("Starting ATS scorer node")
    
    try:
        jd_analysis = state.get("jd_analysis", {})
        matched_skills = state.get("matched_skills", [])
        missing_skills = state.get("missing_skills", [])
        skill_evidence = state.get("skill_evidence", {})
        
        required_skills = jd_analysis.get("required_skills", [])
        preferred_skills = jd_analysis.get("preferred_skills", [])
        tools = jd_analysis.get("tools", [])
        
        # Combine all skills
        all_jd_skills = list(dict.fromkeys(
            required_skills + preferred_skills + tools
        ))
        
        total_skills = len(all_jd_skills) or 1
        matched_count = len(matched_skills)
        missing_count = len(missing_skills)
        
        logger.debug(f"ATS calculation: {matched_count} matched, {missing_count} missing, {total_skills} total")
        
        # 1. Overall skill coverage score (60%)
        skill_coverage_score = (matched_count / total_skills) * ATS_SKILL_COVERAGE_WEIGHT
        
        # 2. Required skill coverage (25%)
        matched_norm = {normalize_skill(s) for s in matched_skills}
        required_norm = {normalize_skill(s) for s in required_skills}
        
        required_matches = len(matched_norm.intersection(required_norm))
        required_total = len(required_norm) or 1
        
        required_score = (required_matches / required_total) * ATS_REQUIRED_WEIGHT
        
        # 3. Evidence confidence score (15%)
        evidence_scores: List[float] = []
        
        for skill, evidence_items in skill_evidence.items():
            for item in evidence_items:
                score = item.get("score", 0)
                evidence_scores.append(score)
        
        if evidence_scores:
            avg_evidence_score = sum(evidence_scores) / len(evidence_scores)
        else:
            avg_evidence_score = 0
        
        evidence_score = avg_evidence_score * ATS_EVIDENCE_WEIGHT
        
        # 4. Penalty for missing skills
        missing_penalty = min(
            missing_count * ATS_MISSING_SKILL_PENALTY,
            ATS_MAX_PENALTY
        )
        
        # Calculate final score
        ats_score = (
            skill_coverage_score +
            required_score +
            evidence_score -
            missing_penalty
        )
        
        ats_score = round(max(0, min(100, ats_score)), 2)
        
        state["ats_score"] = ats_score
        # Store original ATS score for comparison with optimized version
        if "original_ats_score" not in state:
            state["original_ats_score"] = ats_score
        
        state["ats_breakdown"] = {
            "skill_coverage_score": round(skill_coverage_score, 2),
            "required_score": round(required_score, 2),
            "evidence_score": round(evidence_score, 2),
            "missing_penalty": round(missing_penalty, 2),
            "matched_count": matched_count,
            "missing_count": missing_count,
            "total_jd_skills": total_skills,
            "average_evidence_score": round(avg_evidence_score, 3)
        }
        
        logger.info(f"ATS score calculated: {ats_score}/100")
        
    except Exception as e:
        logger.error(f"ATS scorer node failed: {e}", exc_info=True)
        raise
    
    return state