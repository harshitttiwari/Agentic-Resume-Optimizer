"""
Constants and configuration values used throughout the application.
"""

from enum import Enum
from typing import Dict, Any

# ============================================================
# File and Export Settings
# ============================================================

SUPPORTED_RESUME_FORMATS = ["pdf", "docx", "txt"]
SUPPORTED_EXPORT_FORMATS = ["docx", "pdf", "txt"]

OUTPUT_DIR = "outputs"
DEFAULT_EXPORT_FORMAT = "docx"

# ============================================================
# Resume Validation
# ============================================================

MIN_RESUME_LENGTH = 100  # characters
MAX_RESUME_LENGTH = 100000
MIN_JD_LENGTH = 50
MAX_JD_LENGTH = 50000
MIN_TARGET_ROLE_LENGTH = 1
MAX_TARGET_ROLE_LENGTH = 200

# ============================================================
# ATS Scoring
# ============================================================

ATS_SCORE_THRESHOLD_STRONG = 85
ATS_SCORE_THRESHOLD_GOOD = 70
ATS_SCORE_THRESHOLD_MODERATE = 55

ATS_SKILL_COVERAGE_WEIGHT = 50
ATS_REQUIRED_WEIGHT = 30
ATS_EVIDENCE_WEIGHT = 20
ATS_MISSING_SKILL_PENALTY = 1.5
ATS_MAX_PENALTY = 10.0

# ============================================================
# Skill Matching
# ============================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Adaptive thresholds for semantic similarity
SKILL_MATCH_THRESHOLD_1_WORD = 0.50
SKILL_MATCH_THRESHOLD_2_WORD = 0.44
SKILL_MATCH_THRESHOLD_3PLUS_WORD = 0.38

# Top-K embeddings to consider
TOP_K_EVIDENCE = 3

# ============================================================
# LLM Retry and Rate Limiting
# ============================================================

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 30.0
RETRY_BACKOFF_FACTOR = 2.0

# ============================================================
# Rewrite Attempts
# ============================================================

MAX_REWRITE_ATTEMPTS = 2

# ============================================================
# Quality Review
# ============================================================

MIN_QUALITY_RESUME_LENGTH = 500  # characters

# Quality issue severity
class QualityIssueSeverity(str, Enum):
    """Severity levels for quality issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# ============================================================
# Match Level Classifications
# ============================================================

MATCH_LEVELS = {
    "STRONG": {
        "threshold": ATS_SCORE_THRESHOLD_STRONG,
        "label": "Strong match",
        "recommendation": "Resume is well aligned. Only minor wording improvements are needed."
    },
    "GOOD": {
        "threshold": ATS_SCORE_THRESHOLD_GOOD,
        "label": "Good match",
        "recommendation": "Resume is suitable. Improve keyword placement and evidence clarity."
    },
    "MODERATE": {
        "threshold": ATS_SCORE_THRESHOLD_MODERATE,
        "label": "Moderate match",
        "recommendation": "Resume has relevant experience but needs better alignment with the JD."
    },
    "WEAK": {
        "threshold": 0,
        "label": "Weak match",
        "recommendation": "Resume has low alignment or scoring logic needs inspection."
    },
}

# ============================================================
# Language Model Settings
# ============================================================

# Temperature settings for different use cases
TEMPERATURE_STRICT = 0.0  # For parsing and validation
TEMPERATURE_REASONING = 0.1  # For analysis
TEMPERATURE_CREATIVE = 0.2  # For rewriting
