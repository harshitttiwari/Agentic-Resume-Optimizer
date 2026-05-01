# Agentic Resume Optimizer

AI-based resume optimization project using LangGraph, Groq LLM, semantic skill matching, ATS scoring, hallucination checking, and metric preservation validation.

This project is a personal/basic deployment prototype. It is designed to be clean, explainable, and easy to run locally.

---

## Features

- Upload resume in PDF, DOCX, or TXT format
- Paste job description and target role
- Parse resume into structured JSON
- Analyze job description into required skills, preferred skills, tools, and keywords
- Match skills using semantic embeddings
- Generate ATS score with explainable breakdown
- Rewrite resume for ATS alignment
- Check for hallucinated or unsupported content
- Validate whether important metrics are preserved
- Show before/after keyword coverage comparison
- Export resume only when quality checks pass

---

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

---

## Project Flow

```text
Resume Upload
    ↓
Resume Parser
    ↓
JD Analyzer
    ↓
Skill Matcher
    ↓
ATS Scorer
    ↓
Gap Analyzer
    ↓
Resume Rewriter
    ↓
Truth Checker
    ↓
Quality Reviewer
    ↓
Export if safe

## 🏗️ System Architecture

### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENTIC WORKFLOW                              │
│                    (LangGraph 1.0+ StateGraph)                        │
└─────────────────────────────────────────────────────────────────────┘

  Resume Input              Job Description Input
       │                            │
       └────────────────┬───────────┘
                        │
                   ┌────▼─────┐
                   │  PARSE    │  Node 1: Extract resume structure
                   │  RESUME   │  (cached by SHA-256 hash)
                   └────┬─────┘
                        │
                   ┌────▼─────┐
                   │ ANALYZE   │  Node 2: Extract job requirements
                   │ JOB DESC  │  (cached by SHA-256 hash)
                   └────┬─────┘
                        │
                   ┌────▼───────────┐
                   │ SKILL MATCHER   │  Node 3: Semantic matching
                   │ (Embeddings +   │  - Sentence Transformers
                   │  LLM Fallback)  │  - Adaptive thresholds
                   └────┬───────────┘  - Evidence collection
                        │
                   ┌────▼──────────┐
                   │ ATS SCORER     │  Node 4: Calculate compatibility
                   │ (Weighted:     │  - 60% skill coverage
                   │  60+25+15)     │  - 25% required skills
                   └────┬──────────┘  - 15% evidence confidence
                        │              - Penalties for missing skills
                   ┌────▼─────┐
                   │GAP        │  Node 5: Identify missing skills
                   │ANALYZER   │  Generate recommendations
                   └────┬─────┘
                        │
       ┌─────────────────┴──────────────────┐
       │                                    │
  ┌────▼───────────┐              ┌────────▼────────┐
  │ RESUME REWRITER │  Retry Loop  │ QUALITY REVIEW  │
  │ (ATS Optimize)  │◄─────────────│ (Multi-checks)  │
  └────┬───────────┘  (up to 3x)   └────────┬────────┘
       │                                    │
  ┌────▼─────────────┐                     │
  │ TRUTH CHECKER    │◄────────────────────┘
  │ (Hallucination   │  Quality issues?
  │  Detection)      │  Try rewrite again
  └────┬─────────────┘
       │
  ┌────▼─────────────────────────┐
  │ Decision Node:                │
  │ - Truthful + Quality OK?      │◄─────┐
  │   → Export                    │      │
  │ - Hallucination detected?     │      │
  │   → Retry Rewrite (Loop)      │      │
  │ - Quality issues?             │      │
  │   → Retry Rewrite (Loop)      │──────┘
  └────┬─────────────────────────┘
       │
  ┌────▼──────────────┐
  │ FINAL EXPORT      │
  │ + Metrics Report  │
  │ + ATS Comparison  │
  │ + Skill Evidence  │
  └────┬──────────────┘
       │
  Optimized Resume + Full Analysis Bundle
```

