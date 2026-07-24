"""Tests for app/utils.py — URL, JSON, and timestamp helpers."""
import json

from app.utils import (
    date_only,
    extract_domain,
    normalize_url,
    now_compact,
    parse_json,
    safe_extract_json_array,
)


def test_normalize_url_adds_https_when_missing():
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("example.com/path") == "https://example.com/path"


def test_normalize_url_preserves_existing_scheme():
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("http://example.com") == "http://example.com"


def test_extract_domain_strips_path_and_scheme():
    assert extract_domain("https://www.example.com/foo/bar") == "www.example.com"
    assert extract_domain("https://example.com") == "example.com"


def test_extract_domain_handles_garbage_input():
    # Falls back to the input string instead of raising.
    assert extract_domain("") == ""


def test_parse_json_plain():
    assert parse_json('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_parse_json_strips_markdown_fences():
    raw = '```json\n{"score": 89}\n```'
    assert parse_json(raw) == {"score": 89}


def test_parse_json_handles_empty_string():
    import pytest
    with pytest.raises(json.JSONDecodeError):
        parse_json("")


def test_safe_extract_json_array_finds_first_list():
    raw = 'Here are the FAQs: ["What is AEO?", "How does it work?"] — thanks!'
    assert safe_extract_json_array(raw) == ["What is AEO?", "How does it work?"]


def test_safe_extract_json_array_returns_empty_when_no_list():
    assert safe_extract_json_array("nothing to see here") == []


def test_now_compact_format():
    s = now_compact()
    # YYYYMMDD_HHMMSS = 8 + 1 + 6 = 15 chars
    assert len(s) == 15
    assert s[8] == "_"
    assert s[:8].isdigit()
    assert s[9:].isdigit()


def test_date_only_slices_iso_timestamp():
    assert date_only("2026-07-24T10:30:00") == "2026-07-24"
    assert date_only("2026-07-24T10:30:00.123456") == "2026-07-24"
    assert date_only("") == ""
