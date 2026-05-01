# Agentic Resume Optimizer

AI-powered resume optimization tool built with LangGraph and Streamlit. It parses a resume, analyzes the job description, matches skills, scores ATS fit, checks for unsupported claims, and rewrites the resume for a target role.

![Agentic Resume Optimizer workflow graph](graph/workflow.png)

The image above is the exact project graph rendered from [graph/workflow.png](graph/workflow.png).

---

## What It Does

Give it a resume, a job description, and a target role. The app then:

1. Parses the resume into structured content.
2. Analyzes the job description for required and preferred skills.
3. Matches skills using semantic search and LLM-backed reasoning.
4. Calculates an ATS-style score with a breakdown.
5. Identifies missing skills and content gaps.
6. Rewrites the resume to better fit the role.
7. Checks for hallucinations and missing metric preservation.
8. Exports the final result only when the quality checks are acceptable.

## Why This Matters

This project shows how a multi-step AI system is assembled from smaller, testable nodes instead of one large prompt and it also demonstrates practical software engineering skills:

- Real workflow orchestration with LangGraph.
- Clear input validation and output checks.
- Explainable ATS scoring instead of a black-box result.
- Resume rewriting with safety checks before export.
- Local, reproducible execution with a simple Streamlit front end.

## Core Features

- Upload resume in PDF, DOCX, or TXT format
- Paste job description and target role
- Parse resume into structured JSON
- Analyze job description into required skills, preferred       skills, tools, and keywords
- Match skills using semantic embeddings
- Generate ATS score with explainable breakdown
- Rewrite resume for ATS alignment
- Check for hallucinated or unsupported content
- Validate whether important metrics are preserved
- Show before/after keyword coverage comparison
- Export resume only when quality checks pass

---

## How The Workflow Works

The graph is intentionally linear at the start and guarded at the end:

- Resume upload and parsing happen first.
- Job description analysis and skill matching run next.
- ATS scoring and gap analysis produce the main comparison data.
- Resume rewriting improves the draft.
- Truth checking and quality review decide whether the resume is safe to export.

This keeps the system understandable, debuggable, and easier to trust.

## Tech Stack

- Python
- Streamlit
- LangGraph
- LangChain Groq
- Sentence Transformers
- PyMuPDF
- python-docx
- ReportLab
- Pydantic
- JSON file caching

## Project Layout

- `app_v2.py` - Streamlit user interface
- `main.py` - orchestration entry point for the workflow
- `graph/` - LangGraph workflow definition and diagram assets
- `nodes/` - the individual pipeline steps
- `utils/` - file loading, validation, logging, exporting, and helper utilities
- `outputs/` - generated files and exports

## Quick Start

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies with:

	```bash
	pip install -r requirements.txt
	```

4. Create a `.env` file and add your Groq API key:

	```env
	GROQ_API_KEY=your_key_here
	```

5. Start the Streamlit app:

	```bash
	streamlit run app_v2.py
	```

## How To Use

1. Upload a resume in PDF, DOCX, or TXT format.
2. Paste the full job description.
3. Enter the target role.
4. Choose the output format.
5. Click Optimize Resume.
6. Review the ATS score, keyword coverage, skill gaps, quality checks, and final resume.

## Understanding the Analysis

- The app is not only rewriting text. It is building a structured analysis first, then using that analysis to guide the rewrite.
- The ATS score is a compatibility signal, not a guarantee of interview success.
- If the truth checker or quality reviewer fails, the resume is treated as a draft and should be reviewed manually.
- The workflow image at the top is the real graph used by the project, not a simplified illustration.

## Technical Highlights

- The output includes both the optimized resume and the reasoning behind the changes.
- The project is focused on transparent evaluation rather than hidden automation.
- The workflow is modular, so each step can be tested, improved, or replaced independently.
- The quality gates reduce the chance of unsupported claims entering the final resume.

## Output

When the workflow passes quality checks, the app can export the final resume and supporting analysis artifacts. Generated files are written to the local outputs folder.

## Environment

The app expects a valid `GROQ_API_KEY` in the environment or `.env` file before running.

---

## Summary

This project is a compact but complete example of an AI-assisted resume optimization pipeline: structured parsing, semantic matching, ATS scoring, rewrite generation, and safety checks, all shown through an understandable workflow.
