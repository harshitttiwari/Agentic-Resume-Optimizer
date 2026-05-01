"""
Input validation and sanitization utilities.
Ensures all user inputs meet safety and correctness requirements.
"""

from typing import Optional, List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_resume_input(resume_text: str, min_length: int = 100) -> str:
    """
    Validate and sanitize resume text input.
    
    Args:
        resume_text: Raw resume text
        min_length: Minimum acceptable length
        
    Returns:
        Cleaned resume text
        
    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(resume_text, str):
        raise ValueError("Resume must be a string")
    
    resume_text = resume_text.strip()
    
    if len(resume_text) < min_length:
        raise ValueError(f"Resume too short (minimum {min_length} characters)")
    
    if len(resume_text) > 100000:
        logger.warning("Resume is very long (>100k chars), may cause API issues")
    
    logger.info(f"Resume validated: {len(resume_text)} characters")
    return resume_text


def validate_job_description(jd_text: str, min_length: int = 50) -> str:
    """
    Validate and sanitize job description input.
    
    Args:
        jd_text: Raw job description
        min_length: Minimum acceptable length
        
    Returns:
        Cleaned job description
        
    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(jd_text, str):
        raise ValueError("Job description must be a string")
    
    jd_text = jd_text.strip()
    
    if len(jd_text) < min_length:
        raise ValueError(f"Job description too short (minimum {min_length} characters)")
    
    if len(jd_text) > 50000:
        logger.warning("Job description is very long (>50k chars)")
    
    logger.info(f"Job description validated: {len(jd_text)} characters")
    return jd_text


def validate_target_role(role: str) -> str:
    """
    Validate target role input.
    
    Args:
        role: Target role string
        
    Returns:
        Cleaned role string
        
    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(role, str):
        raise ValueError("Target role must be a string")
    
    role = role.strip()
    
    if not role:
        raise ValueError("Target role cannot be empty")
    
    if len(role) > 200:
        raise ValueError("Target role too long (maximum 200 characters)")
    
    logger.info(f"Target role validated: {role}")
    return role


def validate_skills_list(skills: List[str]) -> List[str]:
    """
    Validate and clean skills list.
    
    Args:
        skills: List of skill strings
        
    Returns:
        Cleaned skills list with duplicates removed
    """
    if not isinstance(skills, list):
        raise ValueError("Skills must be a list")
    
    # Convert to strings, strip whitespace, remove empty/duplicates
    cleaned = []
    seen = set()
    
    for skill in skills:
        if not isinstance(skill, str):
            continue
        
        skill = skill.strip()
        if skill and skill.lower() not in seen:
            cleaned.append(skill)
            seen.add(skill.lower())
    
    logger.info(f"Skills list validated: {len(cleaned)} unique skills")
    return cleaned


def validate_export_format(format_str: str) -> str:
    """
    Validate export format.
    
    Args:
        format_str: Export format (docx or pdf)
        
    Returns:
        Validated format string
        
    Raises:
        ValueError: If format is invalid
    """
    format_str = format_str.lower().strip()
    
    if format_str not in ["docx", "pdf", "txt"]:
        raise ValueError(f"Unsupported export format: {format_str}. Use 'docx', 'pdf', or 'txt'")
    
    return format_str
