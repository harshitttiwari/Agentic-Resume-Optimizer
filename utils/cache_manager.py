"""Simple JSON file cache for repeated LLM outputs.

Each cache entry is stored as one JSON file under `.cache`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"


def generate_cache_key(text: str, prefix: str) -> str:
    """Build a stable cache key from input text and cache prefix."""
    payload = f"{prefix}:{(text or '').strip()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def _cache_path(cache_key: str) -> Path:
    """Return full path for a cache key."""
    return CACHE_DIR / f"{cache_key}.json"


def load_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Load cached JSON object, or return None if missing/corrupt."""
    try:
        path = _cache_path(cache_key)

        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

        return None

    except Exception:
        # Cache is optional. If broken, recompute instead of crashing.
        return None


def save_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """Save JSON cache entry. Failure should not block main workflow."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        path = _cache_path(cache_key)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    except Exception:
        # Cache is only an optimization.
        return