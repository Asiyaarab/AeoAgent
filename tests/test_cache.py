"""Tests for app/cache.py — TTL + eviction semantics."""
import time

from app.cache import SimpleCache


def test_set_and_get_round_trip():
    c = SimpleCache(ttl_seconds=60, max_entries=4)
    c.set("https://example.com", {"score": 88})
    assert c.get("https://example.com") == {"score": 88}


def test_get_returns_none_for_missing_key():
    c = SimpleCache(ttl_seconds=60, max_entries=4)
    assert c.get("https://nope.com") is None


def test_url_normalization_for_cache_key():
    """Different forms of the same URL hit the same cache slot."""
    c = SimpleCache(ttl_seconds=60, max_entries=4)
    c.set("https://Example.com/", {"v": 1})
    # case-insensitive scheme/host
    assert c.get("https://example.com") == {"v": 1}
    # trailing slash stripped
    assert c.get("https://example.com/") == {"v": 1}
    # mixed case
    assert c.get("HTTPS://EXAMPLE.com") == {"v": 1}


def test_ttl_expiry():
    c = SimpleCache(ttl_seconds=0, max_entries=4)
    c.set("https://x.com", {"v": 1})
    # TTL of 0s → already expired on the next call
    time.sleep(0.01)
    assert c.get("https://x.com") is None


def test_eviction_at_max_entries():
    c = SimpleCache(ttl_seconds=60, max_entries=2)
    c.set("a.com", 1)
    c.set("b.com", 2)
    c.set("c.com", 3)  # should evict "a.com"
    assert c.get("a.com") is None
    assert c.get("b.com") == 2
    assert c.get("c.com") == 3


def test_stats():
    c = SimpleCache(ttl_seconds=120, max_entries=8)
    c.set("a.com", 1)
    s = c.stats()
    assert s["size"] == 1
    assert s["max"] == 8
    assert s["ttl_seconds"] == 120


def test_clear():
    c = SimpleCache(ttl_seconds=60, max_entries=4)
    c.set("a.com", 1)
    c.clear()
    assert c.get("a.com") is None
