"""
Resume Rewriter Node.

Rewrites resume using only verified information from parsed resume.
Optimizes for ATS keywords and alignment with job description.
"""

import json
from typing import Dict, Any
from config import llm_fast
from prompts import RESUME_REWRITE_PROMPT
from utils.error_handler import retry_on_rate_limit
from utils.logger import get_logger

logger = get_logger(__name__)


@retry_on_rate_limit(max_retries=3)
def call_rewriter_llm(prompt: str) -> str:
    """
    Call LLM for resume rewriting with retry logic.
    
    Args:
        prompt: Formatted rewrite prompt
        
    Returns:
        LLM response content
        
    Raises:
        Exception: If LLM call fails after retries
    """
    llm = llm_fast()
    response = llm.invoke(prompt)
    return response.content


def resume_rewriter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rewrite resume to better match job description while maintaining accuracy.
    
    Performs:
    1. Increment rewrite attempt counter
    2. Build rewrite prompt with context
    3. Call LLM with retry
    4. Update final resume in state
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with rewritten_resume and final_resume
    """
    logger.info("Starting resume rewriter node")
    
    try:
        state["rewrite_attempts"] = state.get("rewrite_attempts", 0) + 1
        attempt_count = state["rewrite_attempts"]
        
        logger.debug(f"Resume rewrite attempt: {attempt_count}")
        
        # Build rewrite prompt
        prompt = RESUME_REWRITE_PROMPT.format(
            raw_resume_text=state.get("raw_resume_text", ""),
            parsed_resume=json.dumps(state.get("parsed_resume", {}), indent=2, ensure_ascii=False),
            jd_analysis=json.dumps(state.get("jd_analysis", {}), indent=2, ensure_ascii=False),
            matched_skills=json.dumps(state.get("matched_skills", []), indent=2, ensure_ascii=False),
            missing_skills=json.dumps(state.get("missing_skills", []), indent=2, ensure_ascii=False),
            target_role=state.get("target_role", "")
        )       
        # Call LLM with retry
        rewritten_text = call_rewriter_llm(prompt)
        
        if not rewritten_text or not rewritten_text.strip():
            raise ValueError("LLM returned empty resume")
        
        state["rewritten_resume"] = rewritten_text
        state["final_resume"] = rewritten_text
        
        logger.info(f"Resume rewriter node completed (attempt {attempt_count})")
        
    except Exception as e:
        logger.error(f"Resume rewriter node failed: {e}", exc_info=True)
        raise
    
    return state