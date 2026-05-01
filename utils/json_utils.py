"""
JSON utilities for safe parsing and error handling.
Centralizes JSON extraction and validation across the application.
"""

import re
import json
from typing import Dict, Any, Optional
from json_repair import loads as repair_loads
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_json_from_response(response_text: str, context: str = "") -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM response safely.
    
    Handles:
    - Markdown code blocks (```json ... ```)
    - JSON wrapped in extra text
    - Malformed JSON (uses json-repair library)
    - Empty responses
    
    Args:
        response_text: Raw LLM response
        context: Context for error messages (e.g., "resume_parser")
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If JSON cannot be extracted or parsed
    """
    if not response_text or not isinstance(response_text, str):
        raise ValueError(f"[{context}] Invalid response: empty or non-string")
    
    response_text = response_text.strip()
    logger.debug(f"[{context}] Extracting JSON from {len(response_text)} chars")
    
    # Remove markdown code blocks
    response_text = re.sub(r"```json\s*", "", response_text)
    response_text = re.sub(r"```\s*", "", response_text)
    response_text = response_text.strip()
    
    # Find JSON boundaries
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    
    if start == -1 or end == 0:
        logger.error(f"[{context}] No JSON object found in response")
        raise ValueError(f"[{context}] No JSON found in LLM response")
    
    json_text = response_text[start:end]
    
    try:
        # Try standard JSON parsing first
        parsed = json.loads(json_text)
        logger.info(f"[{context}] JSON parsed successfully")
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"[{context}] Standard JSON parsing failed: {e}. Attempting repair...")
        try:
            # Fallback to json-repair
            parsed = repair_loads(json_text)
            logger.info(f"[{context}] JSON repaired successfully")
            return parsed
        except Exception as repair_error:
            logger.error(f"[{context}] JSON repair failed: {repair_error}")
            raise ValueError(f"[{context}] JSON parsing failed: {repair_error}")
