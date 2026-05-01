# ================= RESUME PARSER =================
RESUME_PARSER_PROMPT = """
You are a strict resume parser. Return ONLY valid JSON. No markdown, no comments, no trailing commas.

JSON structure (follow exactly):
{{
  "name": null,
  "email": null,
  "phone": null,
  "summary": null,
  "skills": [],
  "projects": [
    {{
      "title": "",
      "description": "",
      "tech_stack": [],
      "impact": null
    }}
  ],
  "experience": [
    {{
      "company": "",
      "role": "",
      "duration": "",
      "bullet_points": []
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": ""
    }}
  ]
}}

Resume Text:
{resume_text}
"""


# ================= JD ANALYZER =================
JD_ANALYZER_PROMPT = """
TASK: Extract and structure job requirements from a job description as valid JSON only. No markdown, no explanation.

RULES:

1. DEDUPLICATION — Normalize casing; collapse synonyms and abbreviations to one canonical entry.
   - "JS", "JavaScript", "javascript" → "JavaScript"

2. ATOMIC SKILLS — Split compound skills joined by "and" or "/".
   - "Reporting and Analysis" → ["Reporting", "Analysis"]
   - Exception: official names like "C++", "iOS/Android"

3. STRIP MODIFIER PHRASES — Extract only the skill name.
   - "experience with X", "knowledge of Y", "familiarity with Z" → X, Y, Z

4. ONLY EXPLICITLY MENTIONED SKILLS — Never infer or assume prerequisites.
   - JD mentions "React" → do NOT add "JavaScript" unless stated

5. CATEGORIZATION (each skill in exactly ONE category):
   - required_skills: core requirements or emphasized/bold items
   - preferred_skills: "nice to have", "preferred", "a plus"
   - tools: specific software/platforms (Excel, Jira, AWS, Salesforce)
   - keywords: methodology/domain terms (Agile, HIPAA, GAAP, Scrum)

6. BROAD VS SPECIFIC — Respect the JD's level of specificity.
   - "any programming language" → "Programming Languages"
   - "Skill A or Skill B" → list both as separate entries

VALIDATION (before returning):
- No duplicates across any array
- No casing variants (e.g. "sql" and "SQL")
- No compound skills with "and" or "/" (unless official names)
- No modifier phrases in skill names

OUTPUT FORMAT (exactly):
{{
  "job_title": "exact title or inferred from content",
  "required_skills": ["Skill1", "Skill2"],
  "preferred_skills": ["Skill3"],
  "tools": ["Tool1"],
  "keywords": ["Keyword1"],
  "notes": "any ambiguities or special cases"
}}

Job Description:
{job_description}
"""


# ================= SKILL CONCEPT EXPANSION =================
SKILL_CONCEPT_EXPANSION_PROMPT = """
Expand the following skill into 4–6 short concept hints for resume matching.

Skill: {skill}

Rules:
- Return JSON only. No markdown.
- Use short phrases (common resume wording, related terms, obvious equivalents).
- Do not invent unrelated skills.

Return format:
{{
  "concepts": ["...", "..."]
}}
"""


# ================= MISSING SKILL SUGGESTIONS =================
MISSING_SKILL_SUGGESTION_PROMPT = """
TASK: Generate short, evidence-based resume bullet suggestions for missing skills.
Use ONLY the provided resume and JD context. Return ONLY valid JSON.

RULES:
1. 1 suggestion per missing skill where possible.
2. Do NOT invent experience, tools, employers, metrics, or outcomes.
3. If resume has supporting evidence → suggest wording that points toward the skill.
4. If no supporting evidence → suggest a neutral learning/exposure/project action.
5. Do not claim the candidate already has the missing skill.

RETURN FORMAT:
{{
  "suggestions": ["...", "..."]
}}

Target Role: {target_role}
Missing Skills: {missing_skills}
Parsed Resume: {parsed_resume}
JD Analysis: {jd_analysis}
"""


# ================= RESUME REWRITE =================
# ================= RESUME REWRITE =================
RESUME_REWRITE_PROMPT = """
Rewrite the resume for ATS alignment while preserving factual accuracy.

Return only the final resume text. No JSON, no explanation, no extra notes.

Strict rules:
- Do not invent companies, roles, projects, skills, tools, certifications, metrics, or achievements.
- Preserve all exact names, technical terms, tools, platforms, software, frameworks, model names, API names, dataset names, standards, certifications, version names, and numeric identifiers.
- If a term looks like a code, model name, API name, version, standard, certification, product name, platform name, or technical identifier, copy it exactly character-for-character.
- Preserve all important numbers: CGPA, grades, percentages, dates, token sizes, latency, accuracy, mAP, counts, financial values, quantities, time values, performance values, and improvement percentages.
- Preserve student/fresher details such as CGPA, 12th percentage, education dates, internship dates, certifications, and project metrics.
- Preserve technical metrics such as 500-token chunks, 50+ documents, 40% improvement, 60% reduction, 82.3% mAP, 80%+ accuracy, sub-100 ms latency, and 100+ items if present in the original resume.
- Do not replace specific tools or terms with generic words.
- Do not compress detailed bullets into vague summaries.
- Improve grammar, action verbs, clarity, and ATS keyword alignment only when supported by resume evidence.
- Keep sections clear: Skills, Projects, Experience, Education.

Important:
Use the Original Resume Text as the source of truth for exact metrics, identifiers, tools, education details, and project facts.

Bad:
Original contains: text-embedding-005
Wrong rewrite: text-embedding-1005

Bad:
Original contains: CGPA: 8.34
Wrong rewrite: education section without CGPA

Good:
Copy exact identifiers and numbers exactly, while improving wording around them.

Original Resume Text:
{raw_resume_text}

Parsed Resume:
{parsed_resume}

JD Analysis:
{jd_analysis}

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Target Role:
{target_role}
"""


# ================= TRUTH CHECK =================
TRUTH_CHECKER_PROMPT = """
Check ONLY for fabricated content in the rewritten resume:
- Companies, projects, or roles not in the original
- Metrics or tools not present in the original

IGNORE: formatting changes, tense changes, keyword additions, categorization differences.

Return JSON ONLY:
{{
  "is_truthful": true,
  "issues": []
}}

Original Resume: {parsed_resume}
Rewritten Resume: {rewritten_resume}
"""