"""
Resume Parser Node.

Parses resume text into structured JSON format using LLM.
Handles multiple resume formats and normalizes data.
"""

from typing import Dict, Any
from config import llm_strict
from prompts import RESUME_PARSER_PROMPT
from schemas import ResumeProfile
from utils.cache_manager import generate_cache_key, load_cache, save_cache
from utils.json_utils import extract_json_from_response
from utils.text_cleaner import clean_resume_text
from utils.error_handler import retry_on_rate_limit
from utils.logger import get_logger

logger = get_logger(__name__)


def safe_join_text(items) -> str:
    """
    Safely join list items into a single string.
    
    Args:
        items: List or single item to join
        
    Returns:
        Cleaned joined string
    """
    if items is None:
        return ""
    
    if isinstance(items, list):
        return " ".join(
            str(item).strip()
            for item in items
            if item is not None and str(item).strip()
        )
    
    return str(items).strip()


def normalize_resume_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize parsed resume JSON structure.
    
    Handles:
    - Skill deduplication
    - Project normalization
    - Experience normalization
    - Education normalization
    
    Args:
        data: Raw parsed resume dict
        
    Returns:
        Normalized resume dict
    """
    logger.info("Normalizing resume JSON structure")
    
    # Normalize skills
    skills = data.get("skills", [])
    normalized_skills = []
    
    for skill in skills:
        if isinstance(skill, dict):
            items = skill.get("items", [])
            normalized_skills.extend(
                str(item).strip()
                for item in items
                if item is not None and str(item).strip()
            )
        elif isinstance(skill, list):
            normalized_skills.extend(
                str(item).strip()
                for item in skill
                if item is not None and str(item).strip()
            )
        elif isinstance(skill, str):
            normalized_skills.append(skill.strip())
    
    data["skills"] = list(dict.fromkeys(normalized_skills))
    logger.debug(f"Normalized {len(data['skills'])} unique skills")
    
    # Normalize projects
    projects = data.get("projects", [])
    normalized_projects = []
    
    for project in projects:
        if not isinstance(project, dict):
            continue
        
        tech_stack = project.get("tech_stack") or project.get("technologies") or []
        
        if isinstance(tech_stack, str):
            tech_stack = [tech_stack]
        
        normalized_projects.append({
            "title": safe_join_text(
                project.get("title") or
                project.get("name") or
                project.get("project_name") or
                "Untitled Project"
            ),
            "description": safe_join_text(project.get("description")),
            "tech_stack": [
                str(tool).strip()
                for tool in tech_stack
                if tool is not None and str(tool).strip()
            ],
            "impact": safe_join_text(project.get("impact")),
        })
    
    data["projects"] = normalized_projects
    logger.debug(f"Normalized {len(normalized_projects)} projects")
    
    # Normalize experience
    experiences = data.get("experience", [])
    normalized_experience = []
    
    for exp in experiences:
        if not isinstance(exp, dict):
            continue
        
        bullet_points = (
            exp.get("bullet_points") or
            exp.get("responsibilities") or
            exp.get("description") or
            []
        )
        
        if isinstance(bullet_points, str):
            bullet_points = [bullet_points]
        
        normalized_experience.append({
            "company": safe_join_text(exp.get("company")),
            "role": safe_join_text(exp.get("role") or exp.get("title")),
            "duration": safe_join_text(exp.get("duration")),
            "bullet_points": [
                str(point).strip()
                for point in bullet_points
                if point is not None and str(point).strip()
            ],
        })
    
    data["experience"] = normalized_experience
    logger.debug(f"Normalized {len(normalized_experience)} experiences")
    
    # Normalize education
    education = data.get("education", [])
    normalized_education = []
    
    for edu in education:
        if isinstance(edu, str):
            normalized_education.append({
                "degree": edu,
                "institution": "",
                "year": "",
            })
        elif isinstance(edu, dict):
            normalized_education.append({
                "degree": safe_join_text(edu.get("degree")),
                "institution": safe_join_text(
                    edu.get("institution") or edu.get("school")
                ),
                "year": safe_join_text(
                    edu.get("year") or edu.get("duration")
                ),
            })
    
    data["education"] = normalized_education
    logger.debug(f"Normalized {len(normalized_education)} education entries")
    
    return data


@retry_on_rate_limit(max_retries=3)
def call_parser_llm(resume_text: str) -> str:
    """
    Call LLM for resume parsing with retry logic.
    
    Args:
        resume_text: Cleaned resume text
        
    Returns:
        LLM response content
        
    Raises:
        Exception: If LLM call fails after retries
    """
    llm = llm_strict()
    prompt = RESUME_PARSER_PROMPT.format(resume_text=resume_text)
    response = llm.invoke(prompt)
    return response.content


def resume_parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse resume text into structured JSON format.
    
    Performs:
    1. Input validation
    2. Text cleaning
    3. LLM parsing with retry
    4. JSON extraction and validation
    5. Data normalization
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with parsed_resume
    """
    logger.info("Starting resume parser node")
    
    try:
        raw_resume_text = state.get("raw_resume_text", "").strip()
        
        if not raw_resume_text:
            raise ValueError("Resume text is empty")
        
        # Clean resume text
        cleaned_resume = clean_resume_text(raw_resume_text)
        logger.debug(f"Cleaned resume: {len(cleaned_resume)} characters")

        # Check cache first so repeated resumes skip the LLM call.
        cache_key = generate_cache_key(cleaned_resume, "resume_parse")
        cached_response = load_cache(cache_key)

        if cached_response is not None:
            logger.info("Resume parser cache hit")
            parsed_json = cached_response
        else:
            response_text = call_parser_llm(cleaned_resume)
            parsed_json = extract_json_from_response(response_text, context="resume_parser")
        
        # Validate BEFORE caching
        resume_profile = ResumeProfile(**parsed_json)
        normalized_data = normalize_resume_json(resume_profile.model_dump())
        
        # Save only clean validated data
        if cached_response is None:
            save_cache(cache_key, normalized_data)
        
        state["parsed_resume"] = normalized_data
        logger.info("Resume parser node completed successfully")
        
    except Exception as e:
        logger.error(f"Resume parser node failed: {e}", exc_info=True)
        raise
    
    return state