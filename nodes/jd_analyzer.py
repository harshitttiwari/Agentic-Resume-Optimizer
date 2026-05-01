"""
Job Description Analyzer Node.

Extracts and analyzes job requirements from job descriptions.
Structures requirements into required skills, preferred skills, and tools.
"""

from typing import Dict, Any
from config import llm_strict
from prompts import JD_ANALYZER_PROMPT
from schemas import JDAnalysis
from utils.cache_manager import generate_cache_key, load_cache, save_cache
from utils.json_utils import extract_json_from_response
from utils.error_handler import retry_on_rate_limit
from utils.logger import get_logger

logger = get_logger(__name__)


@retry_on_rate_limit(max_retries=3)
def call_jd_analyzer_llm(job_description: str) -> str:
    """
    Call LLM for job description analysis with retry logic.
    
    Args:
        job_description: Job description text
        
    Returns:
        LLM response content
        
    Raises:
        Exception: If LLM call fails after retries
    """
    llm = llm_strict()
    prompt = JD_ANALYZER_PROMPT.format(job_description=job_description)
    response = llm.invoke(prompt)
    return response.content


def jd_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze job description and extract structured requirements.
    
    Performs:
    1. Input validation
    2. LLM analysis with retry
    3. JSON extraction and parsing
    4. Validation with Pydantic schema
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with jd_analysis
    """
    logger.info("Starting JD analyzer node")
    
    try:
        job_description = state.get("job_description", "").strip()
        
        if not job_description:
            raise ValueError("Job description is empty")
        
        logger.debug(f"Analyzing job description: {len(job_description)} characters")

        # Check cache first so repeated JDs skip the LLM call.
        cache_key = generate_cache_key(job_description, "jd_analysis")
        cached_response = load_cache(cache_key)

        if cached_response is not None:
            logger.info("JD analyzer cache hit")
            jd_json = cached_response
        else:
            response_text = call_jd_analyzer_llm(job_description)
            jd_json = extract_json_from_response(response_text, context="jd_analyzer")
        
        # Validate BEFORE caching
        validated_jd = JDAnalysis(**jd_json)
        validated_data = validated_jd.model_dump()
        
        # Save only clean validated data
        if cached_response is None:
            save_cache(cache_key, validated_data)
        
        state["jd_analysis"] = validated_data
        logger.info("JD analyzer node completed successfully")
        
    except Exception as e:
        logger.error(f"JD analyzer node failed: {e}", exc_info=True)
        raise
    
    return state