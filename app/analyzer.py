"""
AEO analysis pipeline.

Each function corresponds to one stage of the pipeline:
    1. detect_competitors        — find up to 4 direct competitors
    2. calculate_aeo_score       — score visibility per AI platform
    3. analyze_competitor        — head-to-head comparison
    4. generate_faqs_and_recommendations — FAQs + action plan
    5. run_full_analysis         — orchestrator (the state machine)

The in-memory `current_analysis` dict is the live state object consumed by
the Flask routes. It's the single source of truth for progress + result.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from . import config
from .ai_client import call_ai
from .config import DATA_DIR, REPORT_DIR, get_logger
from .scraper import scrape_website
from .utils import now_compact, now_iso, parse_json, safe_extract_json_array

logger = get_logger(__name__)

# ── In-memory state (single-process; fine for the Streamlit/Flask server) ──
reports_history: list[dict] = []
current_analysis: dict = {}

# Lock guards concurrent writes to the shared dicts
_state_lock = RLock()


# ══════════════════════════════════════════════════════════════════════
# Stage 1 — competitor detection
# ══════════════════════════════════════════════════════════════════════
def detect_competitors(site_data: dict) -> list[str]:
    """Return up to 4 direct competitor URLs detected by the AI."""
    prompt = f"""
Identify the top 4 direct competitors for this website.
Return ONLY a raw JSON array of full URLs. No markdown, no explanation.

Website: {site_data.get('url')}
Title: {site_data.get('title')}
Description: {site_data.get('meta_desc')}
Content: {site_data.get('body_text', '')[:800]}

Output: ["https://competitor1.com", "https://competitor2.com", "https://competitor3.com", "https://competitor4.com"]
"""
    try:
        result = call_ai(prompt)
        urls = safe_extract_json_array(result)
        logger.info("Competitors detected: %s", urls)
        return urls
    except Exception as exc:
        logger.error("Competitor detection failed: %s", exc)
        return []


# ══════════════════════════════════════════════════════════════════════
# Stage 2 — AEO scoring
# ══════════════════════════════════════════════════════════════════════
def calculate_aeo_score(site_data: dict) -> dict:
    """Score the site across ChatGPT / Gemini / Google AI Overview."""
    prompt = f"""
Analyze this website for AEO (Answer Engine Optimization).
Score each AI platform differently — they have different requirements.

ChatGPT favors: conversational Q&A, FAQ content, clear entity definitions, natural language
Gemini favors: structured data schema, Google E-E-A-T signals, authoritative content
Google AI Overview favors: featured snippet optimization, concise direct answers, schema markup

Website: {site_data.get('url')}
Title: {site_data.get('title')}
Meta Description: {site_data.get('meta_desc')}
H1 Tags: {site_data.get('headings', {}).get('h1', [])}
H2 Tags: {site_data.get('headings', {}).get('h2', [])}
Schema Types: {site_data.get('schema_types', [])}
FAQs found: {len(site_data.get('faqs_found', []))}
Word Count: {site_data.get('word_count', 0)}
Images with alt: {site_data.get('imgs_with_alt', 0)} / {site_data.get('imgs_total', 0)}
Internal Links: {site_data.get('internal_links', 0)}
Content: {site_data.get('body_text', '')[:1500]}

Return ONLY this raw JSON (no markdown, no backticks, no explanation):
{{
  "overall_aeo": <weighted average 0-100>,
  "chatgpt_visibility": <0-100 specific to ChatGPT>,
  "gemini_visibility": <0-100 specific to Gemini>,
  "google_ai_overview": <0-100 specific to Google AI Overview>,
  "content_quality": <0-100>,
  "structured_data": <0-100>,
  "conversational_readiness": <0-100>,
  "entity_clarity": <0-100>,
  "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "weaknesses": ["specific weakness 1", "specific weakness 2", "specific weakness 3"],
  "quick_wins": ["quick win 1", "quick win 2", "quick win 3"]
}}
"""
    try:
        result = call_ai(prompt)
        parsed = parse_json(result)
        logger.info(
            "AEO scores: overall=%s chatgpt=%s gemini=%s google=%s",
            parsed.get("overall_aeo"),
            parsed.get("chatgpt_visibility"),
            parsed.get("gemini_visibility"),
            parsed.get("google_ai_overview"),
        )
        return parsed
    except Exception as exc:
        logger.error("AEO score failed, using fallback: %s", exc)
        return _fallback_aeo_score(site_data)


def _fallback_aeo_score(site_data: dict) -> dict:
    """Deterministic heuristic used when the AI call fails."""
    cq = min(site_data.get("word_count", 0) // 20, 100)
    sd = min(len(site_data.get("schema_types", [])) * 25, 100)
    cr = min(len(site_data.get("faqs_found", [])) * 20, 100)
    ec = sum(25 if site_data.get(k) else 0 for k in ("title", "meta_desc", "og_title", "canonical"))
    overall = round((cq + sd + cr + ec) / 4)
    return {
        "overall_aeo": overall,
        "chatgpt_visibility": max(overall - 5, 0),
        "gemini_visibility": min(overall + 3, 100),
        "google_ai_overview": max(overall - 8, 0),
        "content_quality": cq,
        "structured_data": sd,
        "conversational_readiness": cr,
        "entity_clarity": ec,
        "strengths": ["Site is accessible", "Has page title", "Has meta description"],
        "weaknesses": ["Missing FAQ schema", "Low structured data", "Needs conversational content"],
        "quick_wins": ["Add FAQ schema markup", "Improve meta description", "Add H2 headings"],
    }


# ══════════════════════════════════════════════════════════════════════
# Stage 3 — competitor head-to-head
# ══════════════════════════════════════════════════════════════════════
def analyze_competitor(main_site: dict, competitor_data: dict) -> dict:
    """Compare `main_site` against a single competitor."""
    prompt = f"""
Compare these two websites for AEO. Return ONLY valid JSON, no markdown.

MAIN SITE: {main_site.get('url')} | {main_site.get('title')}
Schema: {main_site.get('schema_types')} | Words: {main_site.get('word_count')}
Content: {main_site.get('body_text', '')[:400]}

COMPETITOR: {competitor_data.get('url')} | {competitor_data.get('title')}
Schema: {competitor_data.get('schema_types')} | Words: {competitor_data.get('word_count')}
Content: {competitor_data.get('body_text', '')[:400]}

Return:
{{
  "competitor_url": "{competitor_data.get('url')}",
  "competitor_name": "<short brand name>",
  "their_aeo_score": <0-100>,
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "you_beat_them_on": ["advantage1", "advantage2"],
  "they_beat_you_on": ["their advantage1", "their advantage2"],
  "opportunity": "<one key opportunity to outrank them>"
}}
"""
    try:
        result = call_ai(prompt)
        return parse_json(result)
    except Exception as exc:
        logger.error("Competitor analysis failed for %s: %s",
                     competitor_data.get("url"), exc)
        return {
            "competitor_url": competitor_data.get("url"),
            "competitor_name": "Unknown",
            "error": str(exc),
        }


# ══════════════════════════════════════════════════════════════════════
# Stage 4 — FAQs + recommendations (two parallel-ish AI calls)
# ══════════════════════════════════════════════════════════════════════
def generate_faqs_and_recommendations(site_data: dict, aeo_scores: dict) -> dict:
    """Generate trending FAQs and a strategic action plan."""
    context = f"""Website: {site_data.get('url')}
Title: {site_data.get('title')}
Description: {site_data.get('meta_desc')}
AEO Score: {aeo_scores.get('overall_aeo')}
Weaknesses: {aeo_scores.get('weaknesses', [])}
Content: {site_data.get('body_text', '')[:500]}"""

    faq_prompt = f"""Generate 5 trending FAQs for this website.
Return ONLY valid JSON, no markdown, no backticks.
{context}

Return:
{{
  "trending_faqs": [
    {{"question": "...", "answer": "...", "ai_platform": "ChatGPT"}},
    {{"question": "...", "answer": "...", "ai_platform": "Gemini"}},
    {{"question": "...", "answer": "...", "ai_platform": "Both"}},
    {{"question": "...", "answer": "...", "ai_platform": "Both"}},
    {{"question": "...", "answer": "...", "ai_platform": "ChatGPT"}}
  ]
}}"""

    rec_prompt = f"""Generate AEO recommendations and 30-day plan for this website.
Return ONLY valid JSON, no markdown, no backticks.
{context}

Return:
{{
  "recommendations": [
    {{"priority": "HIGH",   "category": "Structured Data",    "action": "...", "impact": "..."}},
    {{"priority": "HIGH",   "category": "Content",            "action": "...", "impact": "..."}},
    {{"priority": "MEDIUM", "category": "ChatGPT Visibility", "action": "...", "impact": "..."}},
    {{"priority": "MEDIUM", "category": "Gemini Visibility",  "action": "...", "impact": "..."}},
    {{"priority": "LOW",    "category": "Google AI Overview", "action": "...", "impact": "..."}}
  ],
  "content_gaps": ["gap1", "gap2", "gap3"],
  "next_30_day_plan": [
    "week1: specific task",
    "week2: specific task",
    "week3: specific task",
    "week4: specific task"
  ]
}}"""

    result: dict[str, Any] = {
        "trending_faqs": [],
        "recommendations": [],
        "content_gaps": [],
        "next_30_day_plan": [],
    }

    try:
        result.update(parse_json(call_ai(faq_prompt)))
        logger.info("FAQs generated: %d", len(result.get("trending_faqs", [])))
    except Exception as exc:
        logger.error("FAQ generation failed: %s", exc)

    try:
        rec_data = parse_json(call_ai(rec_prompt))
        result["recommendations"]  = rec_data.get("recommendations", [])
        result["content_gaps"]     = rec_data.get("content_gaps", [])
        result["next_30_day_plan"] = rec_data.get("next_30_day_plan", [])
        logger.info("Recommendations generated: %d", len(result.get("recommendations", [])))
    except Exception as exc:
        logger.error("Recommendations generation failed: %s", exc)

    return result


# ══════════════════════════════════════════════════════════════════════
# Stage 5 — full pipeline (state machine + persistence)
# ══════════════════════════════════════════════════════════════════════
def run_full_analysis(target_url: str) -> dict:
    """Run the end-to-end AEO analysis and persist results.

    Updates the global `current_analysis` dict as the run progresses so the
    /api/progress endpoint can stream status to the dashboard.
    """
    global current_analysis
    run_id = now_compact()
    started = datetime.now()

    logger.info("=== AEO Analysis started: %s ===", target_url)
    _set_state(**{
        "status": "running",
        "run_id": run_id,
        "target_url": target_url,
        "started_at": started.isoformat(),
        "progress": "Starting analysis...",
        "progress_pct": 5,
    })

    try:
        # 1 ── Scrape main site
        _set_state(progress="Scraping your website via Scrapfly...", progress_pct=10)
        main_data = scrape_website(target_url)
        if main_data["status"] == "error":
            raise RuntimeError(f"Could not scrape {target_url}: {main_data['error']}")

        # 2 ── Detect competitors
        _set_state(progress="AI detecting your competitors...", progress_pct=25)
        competitor_urls = detect_competitors(main_data)

        # 3 ── AEO scores
        _set_state(progress="Calculating AEO scores (ChatGPT · Gemini · Google AI)...", progress_pct=45)
        aeo_scores = calculate_aeo_score(main_data)

        # 4 ── Per-competitor analysis
        _set_state(progress=f"Analyzing {len(competitor_urls)} competitors...", progress_pct=65)
        competitor_analyses = []
        for cu in competitor_urls[:4]:
            comp_data = scrape_website(cu)
            if comp_data.get("status") == "ok":
                competitor_analyses.append(analyze_competitor(main_data, comp_data))

        # 5 ── FAQs + recommendations
        _set_state(progress="Generating FAQs and recommendations...", progress_pct=85)
        insights = generate_faqs_and_recommendations(main_data, aeo_scores)

        report = {
            "run_id": run_id,
            "target_url": target_url,
            "analyzed_at": started.isoformat(),
            "duration_s": round((datetime.now() - started).total_seconds(), 1),
            "site_data": {k: v for k, v in main_data.items() if k != "body_text"},
            "aeo_scores": aeo_scores,
            "competitors": competitor_analyses,
            "insights": insights,
            "status": "success",
        }

        _persist_report(report)
        _append_history_row(report, aeo_scores)
        _push_history(report, aeo_scores)

        _set_state(**{**report, "status": "success", "progress": "Complete!", "progress_pct": 100})
        logger.info("=== Done! AEO=%s in %ss ===", aeo_scores.get("overall_aeo"), report["duration_s"])
        return report

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        _set_state(**{
            "status": "error",
            "error": str(exc),
            "target_url": target_url,
            "progress": f"Failed: {exc}",
            "progress_pct": 0,
        })
        return {"status": "error", "error": str(exc)}


# ── Private helpers ────────────────────────────────────────────────────
def _set_state(**fields) -> None:
    """Atomically replace fields on the live `current_analysis` dict."""
    global current_analysis
    with _state_lock:
        current_analysis.update(fields)


def _persist_report(report: dict) -> None:
    """Save the full JSON report under reports/report_<run_id>.json."""
    out = REPORT_DIR / f"report_{report['run_id']}.json"
    out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _append_history_row(report: dict, aeo_scores: dict) -> None:
    """Append a single row to data/analysis_history.csv (creating header if needed)."""
    csv_path = DATA_DIR / "analysis_history.csv"
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "run_id", "target_url", "analyzed_at", "duration_s",
            "overall_aeo", "chatgpt_visibility", "gemini_visibility", "google_ai_overview",
        ])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "run_id":             report["run_id"],
            "target_url":         report["target_url"],
            "analyzed_at":        report["analyzed_at"],
            "duration_s":         report["duration_s"],
            "overall_aeo":        aeo_scores.get("overall_aeo", 0),
            "chatgpt_visibility": aeo_scores.get("chatgpt_visibility", 0),
            "gemini_visibility":  aeo_scores.get("gemini_visibility", 0),
            "google_ai_overview": aeo_scores.get("google_ai_overview", 0),
        })


def _push_history(report: dict, aeo_scores: dict) -> None:
    """Prepend the latest run to the in-memory history (capped at 30)."""
    with _state_lock:
        reports_history.insert(0, {
            "run_id":      report["run_id"],
            "target_url":  report["target_url"],
            "analyzed_at": report["analyzed_at"],
            "overall_aeo": aeo_scores.get("overall_aeo", 0),
            "status":      "success",
        })
        if len(reports_history) > 30:
            reports_history.pop()
