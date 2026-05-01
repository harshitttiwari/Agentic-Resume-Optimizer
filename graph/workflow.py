"""
LangGraph Workflow Definition.

Defines the complete resume optimization workflow graph.
Orchestrates all nodes in the correct sequence with conditional routing.
"""

from langgraph.graph import StateGraph, END

from state import ResumeState
from utils.logger import get_logger

from nodes.resume_parser import resume_parser_node
from nodes.jd_analyzer import jd_analyzer_node
from nodes.skill_matcher import skill_matcher_node
from nodes.ats_scorer import ats_scorer_node
from nodes.gap_analyzer import gap_analyzer_node
from nodes.resume_rewriter import resume_rewriter_node
from nodes.truth_checker import truth_checker_node
from nodes.quality_reviewer import quality_reviewer_node

logger = get_logger(__name__)

MAX_REWRITE_ATTEMPTS = 2


def truth_check_router(state: ResumeState) -> str:
    """
    Route based on truth check results.

    If truthful, proceed to quality review.
    If not truthful and retries remain, rewrite.
    If max retries reached, proceed to quality review but keep output unsafe.
    """
    report = state.get("hallucination_report", {})
    attempts = state.get("rewrite_attempts", 0)

    is_truthful = report.get("is_truthful", False)

    if is_truthful:
        logger.info("Truth check passed, proceeding to quality review")
        return "quality_reviewer"

    if attempts >= MAX_REWRITE_ATTEMPTS:
        logger.warning("Max rewrite attempts reached after truth failure; sending to quality review as draft")
        state["export_status"] = "draft_needs_review"
        return "quality_reviewer"

    logger.info(
        f"Truth check failed (attempt {attempts}/{MAX_REWRITE_ATTEMPTS}), retrying rewrite"
    )
    return "resume_rewriter"


def quality_router(state: ResumeState) -> str:
    """
    Route based on quality review results.

    If quality and truth checks pass, mark ready.
    If checks fail and attempts remain, rewrite.
    If max retries reached, finish as draft_needs_review.
    """
    quality_report = state.get("quality_report", {})
    hallucination_report = state.get("hallucination_report", {})
    attempts = state.get("rewrite_attempts", 0)

    is_ready = quality_report.get("is_ready_for_export", False)
    is_truthful = hallucination_report.get("is_truthful", False)

    if is_ready and is_truthful:
        logger.info("Quality and truth checks passed, ready for export")
        state["export_status"] = "ready"
        return END

    if attempts >= MAX_REWRITE_ATTEMPTS:
        logger.warning("Max rewrite attempts reached; marking output as draft_needs_review")

        state["export_status"] = "draft_needs_review"

        quality_report.setdefault("issues", []).append(
            "Max rewrite attempts reached. Output should be manually reviewed before use."
        )
        quality_report["is_ready_for_export"] = False
        state["quality_report"] = quality_report

        return END

    logger.info(
        f"Quality issues found (attempt {attempts}/{MAX_REWRITE_ATTEMPTS}), retrying rewrite"
    )
    return "resume_rewriter"


def build_resume_graph() -> any:
    """
    Build the complete LangGraph workflow.
    """
    logger.info("Building resume optimization workflow graph")

    graph = StateGraph(ResumeState)

    graph.add_node("resume_parser", resume_parser_node)
    graph.add_node("jd_analyzer", jd_analyzer_node)
    graph.add_node("skill_matcher", skill_matcher_node)
    graph.add_node("ats_scorer", ats_scorer_node)
    graph.add_node("gap_analyzer", gap_analyzer_node)
    graph.add_node("resume_rewriter", resume_rewriter_node)
    graph.add_node("truth_checker", truth_checker_node)
    graph.add_node("quality_reviewer", quality_reviewer_node)

    graph.set_entry_point("resume_parser")

    graph.add_edge("resume_parser", "jd_analyzer")
    graph.add_edge("jd_analyzer", "skill_matcher")
    graph.add_edge("skill_matcher", "ats_scorer")
    graph.add_edge("ats_scorer", "gap_analyzer")
    graph.add_edge("gap_analyzer", "resume_rewriter")
    graph.add_edge("resume_rewriter", "truth_checker")

    graph.add_conditional_edges(
        "truth_checker",
        truth_check_router,
        {
            "quality_reviewer": "quality_reviewer",
            "resume_rewriter": "resume_rewriter",
        },
    )

    graph.add_conditional_edges(
        "quality_reviewer",
        quality_router,
        {
            END: END,
            "resume_rewriter": "resume_rewriter",
        },
    )

    logger.info("Workflow graph built successfully")
    return graph.compile()