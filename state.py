from typing import TypedDict, List, Dict, Any, Optional


class ResumeState(TypedDict):
    raw_resume_text: str
    job_description: str
    target_role: str

    parsed_resume: Dict[str, Any]
    jd_analysis: Dict[str, Any]

    matched_skills: List[str]
    missing_skills: List[str]
    ats_score: float
    original_ats_score: float

    gap_report: Dict[str, Any]
    missing_skill_suggestions: List[str]
    rewritten_resume: str

    hallucination_report: Dict[str, Any]
    quality_report: Dict[str, Any]
    metric_report: Dict[str, Any]
    ats_comparison: Dict[str, Any]

    final_resume: str
    export_path: Optional[str]
    export_status: str 

    rewrite_attempts: int
    skill_evidence: Dict[str, List[Dict[str, Any]]]
    ats_breakdown: Dict[str, Any]