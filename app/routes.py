"""
Flask routes for the AEO Agent.

All endpoints are JSON except:
    GET  /                — serves the dashboard HTML
    GET  /api/download/*  — streams an Excel or PDF report as attachment
"""
from __future__ import annotations

from threading import Thread

from flask import Blueprint, jsonify, render_template, request

from . import analyzer
from . import scheduler as sched
from .reports import build_excel_report, build_pdf_report

api = Blueprint("api", __name__)


# ══════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════
@api.route("/")
def index():
    return render_template("dashboard.html")


# ══════════════════════════════════════════════════════════════════════
# Analysis
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/analyze", methods=["POST"])
def api_analyze():
    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400

    sched.set_scheduled_url(url)
    Thread(target=analyzer.run_full_analysis, args=(url,), daemon=True).start()
    return jsonify({"status": "started", "url": url})


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
# Downloads
# ══════════════════════════════════════════════════════════════════════
@api.route("/api/download/excel")
def download_excel():
    return build_excel_report()


@api.route("/api/download/pdf")
def download_pdf():
    return build_pdf_report()
