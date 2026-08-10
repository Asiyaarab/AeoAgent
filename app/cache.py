"""
Tiny in-memory TTL cache for analysis results.

A simple URL → report cache so that re-clicking "Analyze Now" within
``CACHE_TTL_SECONDS`` returns the previous report instead of burning
Scrapfly + Z.ai credits for the exact same input.
"""
from __future__ import annotations

import os
import time
from threading import RLock
from typing import Any

CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))  # 10 min default
CACHE_MAX_ENTRIES: int = int(os.getenv("CACHE_MAX_ENTRIES", "32"))


class SimpleCache:
    """Thread-safe dict + TTL — nothing fancy."""

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS, max_entries: int = CACHE_MAX_ENTRIES):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._lock = RLock()
        self._store: dict[str, tuple[float, Any]] = {}

    @staticmethod
    def _key(url: str) -> str:
        return url.strip().lower().rstrip("/")

    def get(self, url: str) -> Any | None:
        key = self._key(url)
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, url: str, value: Any) -> None:
        key = self._key(url)
        with self._lock:
            # Evict oldest if we'd exceed cap
            if key not in self._store and len(self._store) >= self._max:
                oldest_key = next(iter(self._store))
                self._store.pop(oldest_key, None)
            self._store[key] = (time.time() + self._ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"size": len(self._store), "max": self._max, "ttl_seconds": self._ttl}


# Module-level singleton
analysis_cache = SimpleCache()
