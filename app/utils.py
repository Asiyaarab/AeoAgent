"""
Utility helpers shared across the AEO Agent app.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from .config import get_logger

logger = get_logger(__name__)


# ── JSON helpers ────────────────────────────────────────────────────────
def parse_json(raw: str) -> Any:
    """Safely parse JSON from AI response, stripping markdown fences.

    Raises:
        json.JSONDecodeError: if the cleaned string is not valid JSON.
    """
    clean = re.sub(r"```json|```", "", raw or "").strip()
    return json.loads(clean)


def safe_extract_json_array(raw: str) -> list[str]:
    """Find the first [...] block in a string and parse it as a JSON list."""
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as exc:
        logger.error("Failed to extract JSON array: %s", exc)
        return []


# ── URL helpers ─────────────────────────────────────────────────────────
def normalize_url(url: str) -> str:
    """Prepend https:// if no scheme is present."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def extract_domain(url: str) -> str:
    """Return the bare domain from a URL (e.g. https://x.com/y -> x.com)."""
    try:
        return urlparse(url).netloc
    except Exception:
        return url


# ── Timestamp helpers ──────────────────────────────────────────────────
def now_iso() -> str:
    """Current local time as ISO-8601 string."""
    return datetime.now().isoformat()


def now_compact() -> str:
    """Current time as YYYYMMDD_HHMMSS, useful for filenames and run IDs."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def date_only(iso_ts: str) -> str:
    """Take the date portion of an ISO timestamp (YYYY-MM-DD)."""
    return (iso_ts or "")[:10]
