"""
LLM configuration (minimal).

This project uses Groq for all LLM calls to keep the setup simple.
"""

import os
from typing import Any
from utils.logger import get_logger
from utils.constants import TEMPERATURE_CREATIVE

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

load_dotenv()
logger = get_logger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_FAST_MODEL = "llama-3.1-8b-instant"
# GROQ_FAST_MODEL = "openai/gpt-oss-120b"
# GROQ_FAST_MODEL = "llama-3.3-70b-versatile"


def groq_fast() -> Any:
    """Return the Groq model used across all pipeline steps."""
    if ChatGroq is None:
        raise ImportError(
            "langchain_groq is not installed. Install project dependencies to use LLM features."
        )

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found. Please set it in .env file")

    logger.info("Initializing Groq model")
    return ChatGroq(
        model=GROQ_FAST_MODEL,
        temperature=TEMPERATURE_CREATIVE,
        api_key=GROQ_API_KEY,
    )


def llm_strict() -> Any:
    """Strict model alias (kept for existing node imports)."""
    return groq_fast()


def llm_fast() -> Any:
    """Fast model alias (kept for existing node imports)."""
    return groq_fast()