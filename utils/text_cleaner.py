import re


def clean_text(text: str) -> str:
    """Basic text cleaning."""
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def normalize_bullets(text: str) -> str:
    """Normalize bullet symbols."""
    bullet_symbols = ["•", "●", "▪", "–", "—"]

    for symbol in bullet_symbols:
        text = text.replace(symbol, "-")

    return text


def clean_resume_text(text: str) -> str:
    """Clean extracted resume text."""
    text = normalize_bullets(text)
    text = clean_text(text)

    return text