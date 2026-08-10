"""
Thin wrapper around the Z.ai Chat Completions API (OpenAI-compatible).

Centralizes request shape, headers, error handling, and the model name so
the rest of the app can call `call_ai(prompt, system=...)` without worrying
about transport details.
"""
from __future__ import annotations

import requests

from .config import (
    Z_AI_API_KEY,
    Z_AI_BASE_URL,
    Z_AI_MODEL,
    get_logger,
)

logger = get_logger(__name__)

DEFAULT_SYSTEM = (
    "You are an expert SEO and AEO analyst. "
    "Always respond with valid JSON only — no markdown, no backticks, no commentary."
)


def call_ai(prompt: str, system: str = "", *,
            max_tokens: int = 4000, temperature: float = 0.3) -> str:
    """Call the Z.ai API and return the raw assistant text.

    Raises:
        RuntimeError: if the API key is missing.
        requests.HTTPError: on non-2xx response.
    """
    if not Z_AI_API_KEY:
        raise RuntimeError("Z_AI_API_KEY missing from .env file")

    payload = {
        "model": Z_AI_MODEL,
        "messages": [
            {"role": "system", "content": system or DEFAULT_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Z_AI_API_KEY}",
    }

    response = requests.post(
        f"{Z_AI_BASE_URL}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )

    logger.info("Z.ai API status: %d", response.status_code)
    if response.status_code != 200:
        logger.error("Z.ai error: %s", response.text[:300])
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    logger.info("Z.ai response preview: %s", content[:200])
    return content
