"""
Main entry point for Agentic Resume Optimizer.

Orchestrates the full resume optimization workflow:
1. Input validation
2. Resume parsing
3. Job description analysis
4. Skill matching & ATS scoring
5. Resume rewriting & quality checks
6. Export
"""

from typing import Dict, Any
from graph.workflow import build_resume_graph
from utils.file_loader import load_resume_file
from utils.exporter import export_resume
from utils.validation import (
    validate_resume_input,
    validate_job_description,
    validate_target_role,
    validate_export_format
)
from utils.logger import get_logger

logger = get_logger(__name__)


def run_resume_optimizer(
    resume_file_path: str,
    job_description: str,
    target_role: str,
    export_format: str = "docx",
) -> Dict[str, Any]:
    """
    Run full Agentic Resume Optimizer workflow.
    
    Performs comprehensive resume optimization:
    1. Validates all inputs
    2. Loads and cleans resume
    3. Builds and executes LangGraph workflow
    4. Exports optimized resume
    
    Args:
        resume_file_path: Path to resume file (PDF, DOCX, or TXT)
        job_description: Full job description text
        target_role: Target job role/title
        export_format: Output format (docx, pdf, txt)
        
    Returns:
        Final state dictionary with all optimization results
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If workflow execution fails
    """
    logger.info("Starting Resume Optimizer")
    try:

        # Validate inputs
        logger.debug("Validating inputs...")
        job_description = validate_job_description(job_description)
        target_role = validate_target_role(target_role)
        export_format = validate_export_format(export_format)
        
        # Load resume
        logger.debug(f"Loading resume from: {resume_file_path}")
        raw_resume_text = load_resume_file(resume_file_path)
        raw_resume_text = validate_resume_input(raw_resume_text)
        
        logger.info("All inputs validated successfully")
        
        # Initialize workflow state
        initial_state = {
            "raw_resume_text": raw_resume_text,
            "job_description": job_description,
            "target_role": target_role,
            
            # Parsing results
            "parsed_resume": {},
            "jd_analysis": {},
            
            # Skill analysis
            "matched_skills": [],
            "missing_skills": [],
            "skill_evidence": {},
            
            # Scoring
            "ats_score": 0.0,
            "original_ats_score": 0.0,
            "ats_breakdown": {},
            
            # Gap analysis
            "gap_report": {},
            "missing_skill_suggestions": [],
            
            # Rewriting
            "rewritten_resume": "",
            "final_resume": "",
            "rewrite_attempts": 0,
            
            # Quality checks
            "hallucination_report": {},
            "quality_report": {},
            "metric_report": {},
            "ats_comparison": {},
            
            # Export
            "export_path": None,
            "export_status": "pending",
        }
        
        # Build and execute workflow
        logger.info("Building workflow graph...")
        app = build_resume_graph()
        
        logger.info("Executing workflow...")
        final_state = app.invoke(initial_state)
        # Final safety status check after workflow execution
        quality_report = final_state.get("quality_report", {})
        hallucination_report = final_state.get("hallucination_report", {})
        
        is_quality_ready = quality_report.get("is_ready_for_export", False)
        is_truthful = hallucination_report.get("is_truthful", False)
        
        if is_quality_ready and is_truthful:
            final_state["export_status"] = "ready"
        else:
            final_state["export_status"] = "draft_needs_review"
                # Export resume
        export_path = None

        if final_state.get("export_status") == "ready":
            logger.info(f"Exporting resume as {export_format}...")

            export_path = export_resume(
                text=final_state["final_resume"],
                output_format=export_format
            )

            final_state["export_path"] = export_path
        else:
            logger.warning(
                "Resume not exported because export_status is not ready. "
                "Current status: %s",
                final_state.get("export_status")
            )
            final_state["export_path"] = None

        logger.info("Resume optimization completed successfully")
        ats_comparison = final_state.get("ats_comparison", {})
        if ats_comparison.get("improvement") is not None:
            logger.info(f"ATS Score: {ats_comparison.get('original_ats_score', 0)}/100 → {ats_comparison.get('optimized_ats_score', 0)}/100 (improvement: {ats_comparison.get('improvement', 0):+.1f})")
        else:
            logger.info(f"Final ATS Score: {final_state['ats_score']}/100")
        logger.info(f"Export path: {export_path}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Resume optimizer failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Example usage
    resume_path = "sample_resume.pdf"
    
    jd = """
    We are hiring an AI/ML Intern with knowledge of Python, Machine Learning,
    LangChain, RAG, LLMs, vector databases, APIs, and cloud deployment.
    The candidate should have experience building AI applications and working
    with tools such as Streamlit, FastAPI, ChromaDB, and Gemini.
    """
    
    try:
        result = run_resume_optimizer(
            resume_file_path=resume_path,
            job_description=jd,
            target_role="AI/ML Intern",
            export_format="docx"
        )
        
        # Display results
        print("\n" + "="*50)
        print("OPTIMIZATION RESULTS")
        print("="*50)
        print(f"\nATS Score: {result['ats_score']}/100")
        print(f"\nMatched Skills ({len(result['matched_skills'])}):")
        for skill in result["matched_skills"]:
            print(f"  ✓ {skill}")
        
        print(f"\nMissing Skills ({len(result['missing_skills'])}):")
        for skill in result["missing_skills"]:
            print(f"  ✗ {skill}")
        
        print(f"\nMatch Level: {result['gap_report'].get('match_level', 'Unknown')}")
        print(f"Recommendation: {result['gap_report'].get('recommendation', 'N/A')}")
        
        print(f"\nQuality Issues: {len(result['quality_report'].get('issues', []))}")
        print(f"Ready for Export: {result['quality_report'].get('is_ready_for_export', False)}")
        
        print(f"\nExported to: {result['export_path']}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)