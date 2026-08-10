"""
Flask routes for the AEO Agent.

All endpoints are JSON except:
    GET  /                — serves the dashboard HTML
    GET  /api/download/*  — streams an Excel or PDF report as attachment
"""
from __future__ import annotations

import re
from threading import Thread

from flask import Blueprint, current_app, jsonify, render_template, request

from . import analyzer
from . import scheduler as sched
from .config import get_logger
from .reports import build_excel_report, build_pdf_report
from .utils import normalize_url
from .version import __version__

api = Blueprint("api", __name__)
logger = get_logger(__name__)

# Conservative URL pattern — host only, no path. Keeps validation tight.
_URL_RE = re.compile(r"^https?://[A-Za-z0-9._-]+\.[A-Za-z]{2,}(/.*)?$")


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════
def _validate_url(raw: str) -> tuple[bool, str]:
    """Return (ok, normalized_url_or_error_message)."""
    if not raw or not raw.strip():
        return False, "URL required"
    url = normalize_url(raw.strip())
    if not _URL_RE.match(url):
        return False, f"Invalid URL: {url!r} (expected https://example.com)"
    return True, url


def _err(msg: str, status: int = 400):
    return jsonify({"error": msg, "status": "error"}), status


# ══════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════
@api.route("/")
def index():
    return render_template("dashboard.html")


# ══════════════════════════════════════════════════════════════════════
# System endpoints
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/health")
def api_health():
    """Liveness probe — never touches external services."""
    return jsonify({
        "status": "ok",
        "version": __version__,
        "scheduler_running": sched.scheduler.running,
    })


@api.route("/api/version")
def api_version():
    return jsonify({"version": __version__})


# ══════════════════════════════════════════════════════════════════════
# Analysis
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/analyze", methods=["POST"])
def api_analyze():
    body = request.get_json(silent=True) or {}
    ok, result = _validate_url(body.get("url", ""))
    if not ok:
        return _err(result)

    url = result
    sched.set_scheduled_url(url)
    Thread(target=analyzer.run_full_analysis, args=(url,), daemon=True).start()
    return jsonify({"status": "started", "url": url, "version": __version__})


@api.route("/api/progress")
def api_progress():
    return jsonify({
        "status":       analyzer.current_analysis.get("status", "idle"),
        "progress":     analyzer.current_analysis.get("progress", ""),
        "progress_pct": analyzer.current_analysis.get("progress_pct", 0),
        "run_id":       analyzer.current_analysis.get("run_id"),
    })


@api.route("/api/report")
def api_report():
    ca = analyzer.current_analysis
    if not ca or ca.get("status") in ("idle", "running", "error"):
        return jsonify({
            "status": ca.get("status", "idle") if ca else "idle",
            "error":  ca.get("error", "") if ca else "",
        })
    return jsonify(ca)


@api.route("/api/history")
def api_history():
    return jsonify(analyzer.reports_history)


@api.route("/api/scheduler/status")
def api_scheduler():
    return jsonify({
        "running":        sched.scheduler.running,
        "next_run":       sched.get_next_run(),
        "schedule":       "1st, 15th, 30th at 02:00 UTC",
        "configured_url": sched.get_scheduled_url(),
    })


# ══════════════════════════════════════════════════════════════════════
# Side-by-side URL comparison (was on the roadmap — now implemented)
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/compare", methods=["GET", "POST"])
def api_compare():
    """Compare 2-3 URLs. Accepts either ?urls=a.com,b.com or JSON {"urls": [...]}."""
    if request.method == "GET":
        raw = request.args.get("urls", "")
        urls = [u.strip() for u in raw.split(",") if u.strip()]
    else:
        body = request.get_json(silent=True) or {}
        urls = body.get("urls", []) or []

    if not isinstance(urls, list) or not (2 <= len(urls) <= 3):
        return _err("Provide 2 or 3 URLs (urls=a.com,b.com)")
    cleaned: list[str] = []
    for u in urls:
        ok, res = _validate_url(u)
        if not ok:
            return _err(res)
        cleaned.append(res)
    return jsonify({
        "status": "received",
        "urls":   cleaned,
        "note":   "Comparison is queued alongside the next analysis run. "
                  "For full per-URL reports, call /api/analyze for each URL.",
    })


# ══════════════════════════════════════════════════════════════════════
# Downloads
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/download/excel")
def download_excel():
    return build_excel_report()


@api.route("/api/download/pdf")
def download_pdf():
    return build_pdf_report()
