"""Minimal Streamlit UI for Agentic Resume Optimizer."""

from __future__ import annotations

import os
import tempfile

import streamlit as st

from main import run_resume_optimizer
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Agentic Resume Optimizer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar() -> None:
    """Render sidebar instructions."""
    with st.sidebar:
        st.header("Instructions")
        st.markdown(
            """
            1. Upload resume in PDF, DOCX, or TXT format.
            2. Paste the full job description.
            3. Enter the target role.
            4. Choose the export format.
            5. Click **Optimize Resume**.
            """
        )


def render_results(result: dict, export_format: str) -> None:
    """Render optimization results."""
    st.success("Optimization completed successfully")
    export_status = result.get("export_status", "unknown")

    if export_status != "ready":
        st.warning(
            "This resume is a draft and needs manual review before use. "
            "Quality or truth checks did not fully pass."
        )
    st.header("Optimization Results")

    # Keyword coverage comparison row
    ats_comparison = result.get("ats_comparison", {})
    original_keyword_score = ats_comparison.get(
        "original_ats_score",
        result.get("ats_score", 0),
    )
    optimized_keyword_score = ats_comparison.get(
        "optimized_ats_score",
        result.get("ats_score", 0),
    )
    keyword_improvement = ats_comparison.get("improvement", 0.0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Original Keyword Score", f"{original_keyword_score:.1f}/100")

    with col2:
        st.metric("Optimized Keyword Score", f"{optimized_keyword_score:.1f}/100")

    with col3:
        improvement_icon = (
            "📈" if keyword_improvement > 0
            else "📉" if keyword_improvement < 0
            else "➡️"
        )
        st.metric(
            "Keyword Improvement",
            f"{keyword_improvement:+.1f}",
            improvement_icon,
        )

    with col4:
        matched_count = len(result.get("matched_skills", []))
        st.metric("Matched Skills", matched_count)

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "Optimized Resume",
            "Skill Analysis",
            "ATS Breakdown",
            "Gap Report",
            "Quality Review",
            "Skill Evidence",
            "Truth Check",
        ]
    )

    # ---------------- TAB 1: Optimized Resume ----------------
    with tab1:
        st.subheader("Final Optimized Resume")
        st.text_area(
            "Resume Content",
            result.get("final_resume", ""),
            height=500,
            disabled=True,
        )

    # ---------------- TAB 2: Skill Analysis ----------------
    with tab2:
        st.subheader("Matched Skills")
        matched_skills = result.get("matched_skills", [])

        if matched_skills:
            for index, skill in enumerate(matched_skills, 1):
                st.write(f"{index}. {skill}")
        else:
            st.info("No matched skills found.")

        st.subheader("Missing Skills")
        missing_skills = result.get("missing_skills", [])

        if missing_skills:
            for index, skill in enumerate(missing_skills, 1):
                st.write(f"{index}. {skill}")
        else:
            st.success("No missing skills detected.")

    # ---------------- TAB 3: ATS Breakdown ----------------
    with tab3:
        st.subheader("Official ATS Score Breakdown")

        official_ats_score = result.get("ats_score", 0)
        st.metric("Official ATS Score", f"{official_ats_score:.1f}/100")

        ats_breakdown = result.get("ats_breakdown", {})

        st.markdown("**Weighted ATS Components**")
        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Skill Coverage Score",
                f"{ats_breakdown.get('skill_coverage_score', 0):.2f}",
            )
            st.metric(
                "Required Skills Score",
                f"{ats_breakdown.get('required_score', 0):.2f}",
            )

        with c2:
            st.metric(
                "Evidence Score",
                f"{ats_breakdown.get('evidence_score', 0):.2f}",
            )
            st.metric(
                "Missing Penalty",
                f"-{ats_breakdown.get('missing_penalty', 0):.2f}",
            )

        st.json(ats_breakdown)

        st.divider()

        st.subheader("Keyword Coverage Before/After Comparison")

        ats_comparison = result.get("ats_comparison", {})

        if ats_comparison:
            comp_cols = st.columns(3)

            with comp_cols[0]:
                st.metric(
                    "Original Keyword Score",
                    f"{ats_comparison.get('original_ats_score', 0):.1f}/100",
                )

            with comp_cols[1]:
                st.metric(
                    "Optimized Keyword Score",
                    f"{ats_comparison.get('optimized_ats_score', 0):.1f}/100",
                )

            with comp_cols[2]:
                improvement = ats_comparison.get("improvement", 0.0)
                improvement_label = (
                    "Improved" if improvement > 0
                    else "Decreased" if improvement < 0
                    else "No change"
                )
                st.metric(
                    "Keyword Improvement",
                    f"{improvement:+.1f}",
                    improvement_label,
                )

            with st.expander("View keyword comparison details"):
                st.json(ats_comparison)
        else:
            st.info("No keyword comparison available.")

        st.caption(
            "Note: Keyword scores are a lightweight before/after comparison. "
            "The official ATS score is calculated separately using weighted skill, required-skill, and evidence scoring."
        )

    # ---------------- TAB 4: Gap Report ----------------
    with tab4:
        st.subheader("Gap Analysis")

        gap_report = result.get("gap_report", {})
        st.json(gap_report)

        if gap_report.get("recommendation"):
            st.info(f"Recommendation: {gap_report['recommendation']}")

        suggestions = result.get("missing_skill_suggestions", [])

        if suggestions:
            st.subheader("Missing Skill Bullet Suggestions")
            for suggestion in suggestions:
                st.write(f"- {suggestion}")

    # ---------------- TAB 5: Quality Review ----------------
    with tab5:
        st.subheader("Quality Review")

        quality_report = result.get("quality_report", {})

        if quality_report.get("is_ready_for_export"):
            st.success("Resume is ready for export.")
        else:
            st.warning("Resume has quality issues.")

        issues = quality_report.get("issues", [])
        suggestions = quality_report.get("suggestions", [])

        if issues:
            st.subheader("Issues")
            for issue in issues:
                st.error(issue)

        if suggestions:
            st.subheader("Suggestions")
            for suggestion in suggestions:
                st.info(suggestion)

        metric_report = quality_report.get("metric_report", {})

        if metric_report:
            st.divider()
            st.subheader("Metric Preservation Report")

            metric_cols = st.columns(3)

            with metric_cols[0]:
                st.metric(
                    "Original Metrics",
                    len(metric_report.get("original_metrics", [])),
                )

            with metric_cols[1]:
                st.metric(
                    "Preserved",
                    len(metric_report.get("preserved_metrics", [])),
                )

            with metric_cols[2]:
                st.metric(
                    "Missing",
                    len(metric_report.get("missing_metrics", [])),
                )

            score = metric_report.get("preservation_score", 0.0)
            is_safe = metric_report.get("is_metric_safe", False)
            safety_label = "Safe" if is_safe else "At Risk"

            st.metric("Preservation Score", f"{score:.1%}", safety_label)

            if metric_report.get("missing_metrics"):
                st.warning("Missing Metrics:")
                for metric in metric_report["missing_metrics"]:
                    st.write(f"- {metric}")

            with st.expander("View full metric report"):
                st.json(metric_report)

    # ---------------- TAB 6: Skill Evidence ----------------
    with tab6:
        st.subheader("Skill Evidence")

        skill_evidence = result.get("skill_evidence", {})

        if skill_evidence:
            for skill, evidence_items in skill_evidence.items():
                with st.expander(f"Evidence for: {skill}"):
                    for item in evidence_items:
                        if isinstance(item, dict):
                            st.write(
                                f"- {item.get('text', '')} "
                                f"(confidence: {item.get('score', 0):.3f})"
                            )
                        else:
                            st.write(f"- {item}")
        else:
            st.info("No skill evidence available.")

    # ---------------- TAB 7: Truth Check ----------------
    with tab7:
        st.subheader("Hallucination / Truthfulness Check")

        hallucination_report = result.get("hallucination_report", {})

        if hallucination_report.get("is_truthful"):
            st.success("No hallucinations detected.")
        else:
            st.warning("Potential hallucinations detected.")

        for issue in hallucination_report.get("issues", []):
            st.error(issue)

        st.json(hallucination_report)

    # ---------------- Download ----------------
    st.divider()

    export_path = result.get("export_path")

    if export_path and os.path.exists(export_path):
        with open(export_path, "rb") as file:
            file_data = file.read()

        st.download_button(
            label=f"Download Optimized Resume ({export_format.upper()})",
            data=file_data,
            file_name=os.path.basename(export_path),
            mime="application/octet-stream",
            use_container_width=True,
        )

        st.success(f"File saved to: {export_path}")


# ---------------- Main UI ----------------

if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY is missing. Set it in your environment before running the app.")
    st.stop()

render_sidebar()

st.title("Agentic Resume Optimizer")
st.markdown("ATS-aware resume tailoring system")
st.divider()

uploaded_resume = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx", "txt"],
)

job_description = st.text_area(
    "Job Description",
    height=220,
    placeholder="Paste the full job posting here",
)

target_role = st.text_input(
    "Target Role",
    placeholder="Example: AI/ML Intern",
)

export_format = st.selectbox(
    "Export Format",
    ["docx", "pdf", "txt"],
)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    optimize_clicked = st.button(
        "Optimize Resume",
        use_container_width=True,
    )

if optimize_clicked:
    errors = []

    if uploaded_resume is None:
        errors.append("Please upload a resume file.")

    if not job_description.strip():
        errors.append("Please paste the job description.")

    if not target_role.strip():
        errors.append("Please enter the target role.")

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    suffix = os.path.splitext(uploaded_resume.name)[1]

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(uploaded_resume.read())
    temp_file.close()

    try:
        with st.spinner("Optimizing resume..."):
            result = run_resume_optimizer(
                resume_file_path=temp_file.name,
                job_description=job_description,
                target_role=target_role,
                export_format=export_format,
            )

        st.session_state["last_result"] = result
        st.session_state["last_export_format"] = export_format

    except Exception as error:
        logger.error("Streamlit optimization failed: %s", error, exc_info=True)
        st.error(f"Error: {error}")

    finally:
        try:
            os.remove(temp_file.name)
        except OSError:
            logger.debug("Failed to remove temp file: %s", temp_file.name)


last_result = st.session_state.get("last_result")

if last_result:
    render_results(
        last_result,
        st.session_state.get("last_export_format", export_format),
    )