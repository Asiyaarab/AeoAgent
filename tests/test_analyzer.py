"""Tests for app/analyzer.py — 5-stage pipeline, fully mocked."""
import json

import pytest

from app import analyzer
from app.cache import analysis_cache
from app.utils import now_compact


# ── Fixtures ───────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _reset_state():
    analyzer.current_analysis = {}
    analyzer.reports_history = []
    analysis_cache.clear()
    yield
    analyzer.current_analysis = {}
    analyzer.reports_history = []
    analysis_cache.clear()


def _scrape_ok(url: str) -> dict:
    return {
        "url": url, "title": f"Title of {url}", "meta_desc": "desc",
        "og_title": "", "canonical": url, "headings": {"h1": ["h"], "h2": [], "h3": []},
        "faqs_found": [], "schema_types": ["Organization"],
        "internal_links": 5, "imgs_total": 2, "imgs_with_alt": 2,
        "body_text": "lorem ipsum", "word_count": 10, "scraped_at": "", "status": "ok",
    }


# ── Tests ─────────────────────────────────────────────────────────────
def test_fallback_aeo_score_deterministic():
    site = {"word_count": 200, "schema_types": ["Article"], "faqs_found": [1, 2, 3],
            "title": "x", "meta_desc": "y", "og_title": "z", "canonical": "c"}
    out = analyzer._fallback_aeo_score(site)
    assert 0 <= out["overall_aeo"] <= 100
    assert out["chatgpt_visibility"] >= 0
    assert out["gemini_visibility"] <= 100
    assert len(out["strengths"]) == 3
    assert len(out["weaknesses"]) == 3
    assert len(out["quick_wins"]) == 3


def test_detect_competitors_parses_json_array(monkeypatch):
    monkeypatch.setattr("app.analyzer.call_ai",
                        lambda *a, **kw: '["https://a.com", "https://b.com"]')
    out = analyzer.detect_competitors(_scrape_ok("https://me.com"))
    assert out == ["https://a.com", "https://b.com"]


def test_detect_competitors_handles_markdown_fences(monkeypatch):
    monkeypatch.setattr("app.analyzer.call_ai",
                        lambda *a, **kw: '```json\n["https://a.com"]\n```')
    assert analyzer.detect_competitors(_scrape_ok("https://me.com")) == ["https://a.com"]


def test_detect_competitors_returns_empty_on_failure(monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("AI down")
    monkeypatch.setattr("app.analyzer.call_ai", boom)
    assert analyzer.detect_competitors(_scrape_ok("https://me.com")) == []


def test_calculate_aeo_score_success(monkeypatch):
    payload = {"overall_aeo": 75, "chatgpt_visibility": 80, "gemini_visibility": 70,
               "google_ai_overview": 75, "content_quality": 70, "structured_data": 80,
               "conversational_readiness": 75, "entity_clarity": 65,
               "strengths": ["s1"], "weaknesses": ["w1"], "quick_wins": ["q1"]}
    monkeypatch.setattr("app.analyzer.call_ai", lambda *a, **kw: json.dumps(payload))
    out = analyzer.calculate_aeo_score(_scrape_ok("https://me.com"))
    assert out["overall_aeo"] == 75
    assert out["strengths"] == ["s1"]


def test_calculate_aeo_score_falls_back_on_failure(monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("network")
    monkeypatch.setattr("app.analyzer.call_ai", boom)
    out = analyzer.calculate_aeo_score(_scrape_ok("https://me.com"))
    assert "overall_aeo" in out
    assert out["overall_aeo"] >= 0  # heuristic value


def test_analyze_competitor_handles_failure(monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("nope")
    monkeypatch.setattr("app.analyzer.call_ai", boom)
    out = analyzer.analyze_competitor(_scrape_ok("https://me.com"),
                                       _scrape_ok("https://competitor.com"))
    assert out["competitor_url"] == "https://competitor.com"
    assert "error" in out


def test_generate_faqs_and_recommendations_merges_calls(monkeypatch):
    faq_json = json.dumps({"trending_faqs": [{"question": "q", "answer": "a",
                                              "ai_platform": "Both"}]})
    rec_json = json.dumps({
        "recommendations": [{"priority": "HIGH", "category": "c", "action": "a", "impact": "i"}],
        "content_gaps": ["g1"],
        "next_30_day_plan": ["week1: do X"],
    })
    monkeypatch.setattr("app.analyzer.call_ai", lambda *a, **kw: faq_json)
    # Second call returns the recs; we need to differentiate by inspecting the prompt
    responses = iter([faq_json, rec_json])

    def gate(prompt, *a, **kw):
        return next(responses)
    monkeypatch.setattr("app.analyzer.call_ai", gate)

    out = analyzer.generate_faqs_and_recommendations(_scrape_ok("https://me.com"),
                                                    {"overall_aeo": 60})
    assert len(out["trending_faqs"]) == 1
    assert len(out["recommendations"]) == 1
    assert out["content_gaps"] == ["g1"]


def test_run_full_analysis_cache_hit(monkeypatch):
    cached_report = {"status": "success", "target_url": "https://me.com",
                     "run_id": "x", "aeo_scores": {"overall_aeo": 90}}
    analysis_cache.set("https://me.com", cached_report)

    # If cache works, scraper should never be called.
    def boom(url):
        raise AssertionError("scrape_website should not be called on cache hit")
    monkeypatch.setattr("app.analyzer.scrape_website", boom)

    out = analyzer.run_full_analysis("https://me.com")
    assert out["status"] == "success"
    assert analyzer.current_analysis.get("cache_hit") is True


def test_run_full_analysis_end_to_end(monkeypatch, tmp_path):
    # Point the auto-created dirs to tmp so the test doesn't litter the repo
    data_dir = tmp_path / "data"
    rep_dir = tmp_path / "reports"
    data_dir.mkdir()
    rep_dir.mkdir()
    monkeypatch.setattr("app.analyzer.DATA_DIR", data_dir)
    monkeypatch.setattr("app.analyzer.REPORT_DIR", rep_dir)

    main = _scrape_ok("https://me.com")
    monkeypatch.setattr("app.analyzer.scrape_website", lambda u: main)
    monkeypatch.setattr("app.analyzer.detect_competitors", lambda *a, **kw: [])
    monkeypatch.setattr("app.analyzer.calculate_aeo_score",
                        lambda *a, **kw: {"overall_aeo": 60, "chatgpt_visibility": 60,
                                          "gemini_visibility": 60, "google_ai_overview": 60,
                                          "content_quality": 60, "structured_data": 60,
                                          "conversational_readiness": 60, "entity_clarity": 60,
                                          "strengths": ["s"], "weaknesses": ["w"], "quick_wins": ["q"]})
    monkeypatch.setattr("app.analyzer.generate_faqs_and_recommendations",
                        lambda *a, **kw: {"trending_faqs": [], "recommendations": [],
                                          "content_gaps": [], "next_30_day_plan": []})

    out = analyzer.run_full_analysis("https://me.com")
    assert out["status"] == "success"
    assert out["target_url"] == "https://me.com"
    assert "duration_s" in out
    assert analyzer.current_analysis["status"] == "success"
    # History was pushed
    assert len(analyzer.reports_history) == 1
    # JSON report was persisted
    report_files = list((tmp_path / "reports").glob("report_*.json"))
    assert len(report_files) == 1


def test_run_full_analysis_error_path(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    rep_dir = tmp_path / "reports"
    data_dir.mkdir()
    rep_dir.mkdir()
    monkeypatch.setattr("app.analyzer.DATA_DIR", data_dir)
    monkeypatch.setattr("app.analyzer.REPORT_DIR", rep_dir)

    def boom(url):
        return {"url": url, "status": "error", "error": "blocked"}
    monkeypatch.setattr("app.analyzer.scrape_website", boom)

    out = analyzer.run_full_analysis("https://bad.com")
    assert out["status"] == "error"
    assert analyzer.current_analysis["status"] == "error"
