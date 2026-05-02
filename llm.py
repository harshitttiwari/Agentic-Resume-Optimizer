"""Groq client and prompts — Agentic Resume Optimizer."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
MODEL_STRONG = os.getenv("GROQ_MODEL_STRONG", "llama-3.3-70b-versatile")


@lru_cache(maxsize=4)
def get_llm(model: str, temperature: float = 0.0) -> Any:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")
    from langchain_groq import ChatGroq
    return ChatGroq(model=model, temperature=temperature, api_key=api_key)


def parse_json(text: str) -> dict[str, Any]:
    text = re.sub(r"```(?:json)?|```", "", str(text or ""), flags=re.IGNORECASE).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("LLM did not return a JSON object.")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
        return obj
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned malformed JSON: {e}") from e


def ask_json(prompt: str, fast: bool = False) -> dict[str, Any]:
    model = MODEL_FAST if fast else MODEL_STRONG
    return parse_json(get_llm(model, 0.0).invoke(prompt).content)


# ── Resume parsing ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=16)
def parse_resume_with_llm(resume_text: str) -> dict[str, Any]:
    prompt = f"""
Return only valid JSON for this resume. Use empty strings or empty lists when a field is absent.
Do not invent or infer any information not explicitly written in the resume.

Schema:
{{
  "name": "",
  "email": "",
  "phone": "",
  "skills": [],
  "projects": [
    {{"title": "", "description": "", "tech_stack": [], "impact": ""}}
  ],
  "experience": [
    {{"company": "", "role": "", "duration": "", "bullet_points": []}}
  ],
  "education": [
    {{"degree": "", "institution": "", "year": ""}}
  ],
  "certifications": []
}}

Resume:
{resume_text[:12000]}
"""
    return ask_json(prompt, fast=True)



# ── JD analysis ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=16)
def analyze_jd_with_llm(job_description: str) -> dict[str, Any]:
    prompt = f"""
Extract job requirements as valid JSON only.
Rules:
- Include only skills, tools, and keywords explicitly written in the job description.
- Do not add skills that are implied but not written.
- Split compound terms: "reporting and analysis" → ["reporting", "analysis"].
- Deduplicate case variants: "Python" and "python" → one entry.

Schema:
{{
  "job_title": "",
  "required_skills": [],
  "preferred_skills": [],
  "tools": [],
  "keywords": [],
  "notes": ""
}}

Job description:
{job_description[:12000]}
"""
    return ask_json(prompt, fast=True)



# ── Resume rewriting ───────────────────────────────────────────────────────────

def rewrite_resume_with_llm(context: dict[str, Any]) -> str:
    """
    Send structured JSON context to the LLM and return the rewritten resume text.
    Output is a JSON envelope: {"resume_text": "..."} to ensure clean parsing.
    """
    repair_section = ""
    if context.get("current_draft"):
        repair_section = f"""
This is a repair pass. Improve the draft below using the feedback — do not start from scratch.

Current draft:
{context["current_draft"][:12000]}

Repair feedback:
{context.get("rewrite_feedback", "")}
"""

    prompt = f"""
You are rewriting a resume to better match a target role.
Return only valid JSON in this exact format:
{{"resume_text": "<full rewritten resume as a single string>"}}

Strict rules:
- Use only facts from the original resume. Do not invent employers, projects, degrees, tools, certifications, metrics, or outcomes.
- Preserve every number, percentage, date, score, latency, URL, version, and named tool exactly as written.
- Keep all original projects, experience entries, and bullets unless they are exact duplicates.
- Do not collapse multiple bullets into one vague bullet.
- Use stronger action verbs and better keyword alignment only where the original fact supports it.
- Do not claim skills from the missing_skills list unless the original resume already demonstrates them.
- Do not add a career summary or objective unless one exists in the original resume.

Input context (JSON):
{json.dumps({
    "target_role":        context["target_role"],
    "matched_skills":     context["matched_skills"],
    "missing_skills":     context["missing_skills"],
    "must_keep_metrics":  context.get("must_keep_metrics", []),
    "jd_analysis":        context["jd_analysis"],
    "parsed_resume":      context["parsed_resume"],
}, ensure_ascii=False)}

{repair_section}
Original resume:
{context["raw_resume_text"][:12000]}
"""
    result = ask_json(prompt)
    resume_text = result.get("resume_text", "")
    if not resume_text:
        raise ValueError("LLM returned empty resume_text in rewrite response.")
    return resume_text


# ── Truth checking ─────────────────────────────────────────────────────────────

def truth_check_with_llm(original_text: str, rewritten_text: str) -> dict[str, Any]:
    prompt = f"""
Check whether the rewritten resume contains any facts not supported by the original.
Ignore differences in formatting, grammar, word order, and stronger phrasing when the underlying fact is supported.
Return JSON only:
{{"is_truthful": true, "issues": []}}

Original resume:
{original_text[:9000]}

Rewritten resume:
{rewritten_text[:9000]}
"""
    try:
        data = ask_json(prompt, fast=True)
        return {
            "is_truthful": bool(data.get("is_truthful")),
            "issues": [str(x) for x in data.get("issues", [])],
        }
    except Exception as exc:
        return {"is_truthful": False, "issues": [f"Truth check failed: {exc}"]}