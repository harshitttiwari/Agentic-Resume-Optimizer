"""
Skill Matcher Node.

Matches required job skills against resume evidence using semantic similarity.
Uses adaptive thresholds and LLM as fallback for borderline cases.
"""

import json
from functools import lru_cache
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer, util
import torch

from config import llm_strict
from prompts import SKILL_CONCEPT_EXPANSION_PROMPT
from utils.constants import (
    EMBEDDING_MODEL,
    SKILL_MATCH_THRESHOLD_1_WORD,
    SKILL_MATCH_THRESHOLD_2_WORD,
    SKILL_MATCH_THRESHOLD_3PLUS_WORD,
    TOP_K_EVIDENCE
)
from utils.error_handler import retry_on_rate_limit
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger(__name__)

# Load embedding model once
_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    """
    Lazily load and cache embedding model.
    
    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model




def extract_evidence_units(parsed_resume: Dict[str, Any]) -> List[str]:
    """
    Extract all evidence units from parsed resume.
    
    Includes:
    - Skills
    - Project titles and descriptions
    - Technology stacks
    - Job roles and bullet points
    
    Args:
        parsed_resume: Parsed resume dictionary
        
    Returns:
        List of unique evidence units
    """
    units = []
    
    # Add skills
    units.extend(parsed_resume.get("skills", []))

    # Add summary/profile text when available
    summary_text = parsed_resume.get("summary")
    if summary_text:
        units.append(summary_text)
    
    # Add project information
    for project in parsed_resume.get("projects", []):
        if project.get("title"):
            units.append(project.get("title", ""))
        if project.get("description"):
            units.append(project.get("description", ""))
        units.extend(project.get("tech_stack", []))
    
    # Add experience information
    for exp in parsed_resume.get("experience", []):
        if exp.get("role"):
            units.append(exp.get("role", ""))
        units.extend(exp.get("bullet_points", []))
    
    # Deduplicate
    cleaned_units = []
    seen = set()
    
    for unit in units:
        unit = clean_text(unit)
        
        if unit and unit.lower() not in seen:
            cleaned_units.append(unit)
            seen.add(unit.lower())
    
    logger.debug(f"Extracted {len(cleaned_units)} evidence units from resume")
    return cleaned_units


def get_adaptive_threshold(skill: str) -> float:
    """
    Get adaptive semantic similarity threshold based on skill specificity.
    
    One-word skills (e.g., "Python", "TensorFlow") require stricter matching.
    Multi-word phrases (e.g., "cloud platforms") allow more semantic flexibility.
    
    Args:
        skill: Skill string
        
    Returns:
        Similarity threshold (0.0-1.0)
    """
    skill = clean_text(skill)
    word_count = len(skill.split())
    
    if word_count == 1:
        return SKILL_MATCH_THRESHOLD_1_WORD
    elif word_count == 2:
        return SKILL_MATCH_THRESHOLD_2_WORD
    else:
        return SKILL_MATCH_THRESHOLD_3PLUS_WORD


@lru_cache(maxsize=256)
def expand_skill_concepts(skill: str) -> List[str]:
    """
    Expand a skill into a small set of dynamic concept hints.

    The expansion is derived from the skill text itself, so it works for new
    domains such as Business Studies, Finance, Healthcare, or Design without
    requiring a hand-maintained alias dictionary.

    Args:
        skill: Skill string

    Returns:
        List of concept hints for matching
    """
    skill = clean_text(skill)
    concepts = [skill]

    try:
        judge = llm_strict()
        prompt = SKILL_CONCEPT_EXPANSION_PROMPT.format(skill=skill)

        response = judge.invoke(prompt)
        response_text = response.content.strip()

        try:
            parsed = json.loads(response_text)
            for item in parsed.get("concepts", []):
                value = clean_text(item)
                if value:
                    concepts.append(value)
        except Exception:
            logger.debug(f"Skill concept expansion returned non-JSON for '{skill}'")

    except Exception as e:
        logger.debug(f"Skill concept expansion failed for '{skill}': {e}")

    # Deduplicate while preserving order.
    deduped: List[str] = []
    seen = set()
    for concept in concepts:
        normalized = concept.lower()
        if normalized not in seen:
            deduped.append(concept)
            seen.add(normalized)

    return deduped


def has_concept_support(jd_skill: str, evidence_items: List[str]) -> bool:
    """
    Check whether any dynamically expanded concept for a skill appears directly
    in the evidence.

    This makes the matcher general-purpose without hardcoding a vocabulary.

    Args:
        jd_skill: Required job skill
        evidence_items: Resume evidence strings

    Returns:
        True if direct concept support is found, otherwise False
    """
    aliases = expand_skill_concepts(jd_skill)
    evidence_text = " ".join(item.lower() for item in evidence_items)

    for alias in aliases:
        if alias and alias in evidence_text:
            logger.debug(f"Direct concept support found for '{jd_skill}' via '{alias}'")
            return True

    return False


@retry_on_rate_limit(max_retries=2)
def llm_borderline_judge(jd_skill: str, evidence_items: List[str]) -> bool:
    """
    Use LLM to judge borderline skill matches.
    
    Only invoked for borderline semantic similarity scores (0.38-0.55).
    Avoids hardcoded mappings and improves generalization.
    
    Args:
        jd_skill: Required job skill
        evidence_items: Resume evidence to evaluate
        
    Returns:
        True if skill is clearly supported, False otherwise
    """
    try:
        judge = llm_strict()
        
        prompt = f"""
You are a strict resume-skill evidence judge.

Question:
Does the resume evidence support the required skill: "{jd_skill}"?

Rules:
- Answer ONLY YES or NO.
- Say YES only if the evidence clearly supports the skill.
- Do not be overly generous.
- Do not infer fake experience.

Resume Evidence:
{evidence_items}
"""
        
        response = judge.invoke(prompt)
        answer = response.content.strip().upper()
        result = answer.startswith("YES")
        
        logger.debug(f"LLM judgment for '{jd_skill}': {result}")
        return result
        
    except Exception as e:
        logger.warning(f"LLM borderline judge failed for '{jd_skill}': {e}. Defaulting to False.")
        return False


def skill_matcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match job requirements skills against resume evidence.
    
    Strategy:
    1. Extract evidence units from parsed resume
    2. Calculate semantic similarity using embeddings
    3. Use adaptive thresholds based on skill specificity
    4. Apply high-confidence margin logic
    5. Use LLM for borderline cases only
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with matched_skills, missing_skills, skill_evidence
    """
    logger.info("Starting skill matcher node")
    
    try:
        parsed_resume = state.get("parsed_resume", {})
        jd_analysis = state.get("jd_analysis", {})
        
        required_skills = jd_analysis.get("required_skills", [])
        preferred_skills = jd_analysis.get("preferred_skills", [])
        tools = jd_analysis.get("tools", [])
        
        jd_skills = list(dict.fromkeys(required_skills + preferred_skills + tools))
        resume_corpus = extract_evidence_units(parsed_resume)
        
        logger.debug(f"Matching {len(jd_skills)} skills against {len(resume_corpus)} resume units")
        
        # Handle empty inputs
        if not jd_skills or not resume_corpus:
            logger.warning("Empty JD skills or resume corpus")
            state["matched_skills"] = []
            state["missing_skills"] = jd_skills
            state["skill_evidence"] = {}
            return state
        
        # Get embedding model
        model = get_embedding_model()
        
        # Encode all skills and resume evidence
        logger.debug("Encoding skills and resume evidence...")
        jd_embeddings = model.encode(jd_skills, convert_to_tensor=True)
        resume_embeddings = model.encode(resume_corpus, convert_to_tensor=True)
        
        matched_skills: List[str] = []
        missing_skills: List[str] = []
        evidence_map: Dict[str, List[Dict[str, Any]]] = {}
        
        # Match each skill
        for i, jd_skill in enumerate(jd_skills):
            jd_vec = jd_embeddings[i]
            similarities = util.cos_sim(jd_vec, resume_embeddings)[0]
            
            # Get top-K similar units
            top_k_count = min(TOP_K_EVIDENCE, len(resume_corpus))
            top_k = torch.topk(similarities, k=top_k_count)
            
            top_scores = top_k.values.tolist()
            top_indices = top_k.indices.tolist()
            
            best_score = top_scores[0]
            second_score = top_scores[1] if len(top_scores) > 1 else 0.0
            margin = best_score - second_score
            
            threshold = get_adaptive_threshold(jd_skill)
            
            # Collect evidence
            evidence_items = [
                {
                    "text": resume_corpus[idx],
                    "score": round(top_scores[j], 3)
                }
                for j, idx in enumerate(top_indices)
            ]
            
            evidence_text_only = [item["text"] for item in evidence_items]
            
            is_match = False
            match_reason = ""

            # 0. Direct concept support from dynamic expansion
            if has_concept_support(jd_skill, evidence_text_only):
                is_match = True
                match_reason = "Direct concept support found in resume evidence"
            
            # Matching logic with fallback chain
            elif best_score >= threshold:
                # 1. Strong semantic match
                is_match = True
                match_reason = f"Strong semantic match ({best_score:.3f} >= {threshold:.3f})"
                
            elif best_score >= 0.50 and margin >= 0.08:
                # 2. High-confidence margin match
                is_match = True
                match_reason = f"High margin match ({best_score:.3f} with margin {margin:.3f})"
                
            elif len(top_scores) >= 2 and top_scores[0] >= 0.42 and top_scores[1] >= 0.38:
                # 3. Multiple medium evidence points
                is_match = True
                match_reason = f"Multiple medium evidence ({top_scores[0]:.3f}, {top_scores[1]:.3f})"
                
            elif 0.38 <= best_score < threshold:
                # 4. LLM fallback for borderline cases
                is_match = llm_borderline_judge(
                    jd_skill=jd_skill,
                    evidence_items=evidence_text_only
                )
                match_reason = f"LLM judgment (borderline: {best_score:.3f})"
            
            # Record result
            if is_match:
                matched_skills.append(jd_skill)
                evidence_map[jd_skill] = evidence_items
                logger.debug(f"✓ Matched '{jd_skill}': {match_reason}")
            else:
                missing_skills.append(jd_skill)
                logger.debug(f"✗ Missing '{jd_skill}': {best_score:.3f} < {threshold:.3f}")
        
        state["matched_skills"] = matched_skills
        state["missing_skills"] = missing_skills
        state["skill_evidence"] = evidence_map
        
        logger.info(
            f"Skill matching completed: "
            f"{len(matched_skills)} matched, {len(missing_skills)} missing"
        )
        
    except Exception as e:
        logger.error(f"Skill matcher node failed: {e}", exc_info=True)
        raise
    
    return state