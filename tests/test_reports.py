"""Tests for app/reports.py — Excel + PDF report builders (no AI calls)."""
import io

import pytest

from app import analyzer
from app.reports import build_excel_report, build_pdf_report


SAMPLE_REPORT = {
    "status": "success",
    "run_id": "20260116_102430",
    "target_url": "https://example.com",
    "analyzed_at": "2026-01-16T10:24:30",
    "duration_s": 12.3,
    "aeo_scores": {
        "overall_aeo": 78,
        "chatgpt_visibility": 82,
        "gemini_visibility": 75,
        "google_ai_overview": 70,
        "content_quality": 80,
        "structured_data": 65,
        "conversational_readiness": 70,
        "entity_clarity": 78,
        "strengths": ["Has clear schema", "Strong meta tags", "FAQ section present"],
        "weaknesses": ["Slow page", "Few internal links", "No H2 on home"],
        "quick_wins": ["Add FAQ schema", "Compress images", "Write a blog"],
    },
    "competitors": [
        {
            "competitor_name": "Comp One",
            "competitor_url": "https://comp1.com",
            "their_aeo_score": 65,
            "strengths": ["Good content", "Has blog"],
            "weaknesses": ["Slow site"],
            "opportunity": "Outrank with a fresher FAQ page",
        },
    ],
    "insights": {
        "trending_faqs": [
            {"question": "What is X?", "answer": "X is a thing.", "ai_platform": "ChatGPT"},
            {"question": "How does Y work?", "answer": "Y works by...", "ai_platform": "Gemini"},
        ],
        "recommendations": [
            {"priority": "HIGH", "category": "Schema", "action": "Add FAQPage schema",
             "impact": "Higher AI Overview inclusion"},
            {"priority": "MEDIUM", "category": "Content", "action": "Add 5 FAQs",
             "impact": "Better ChatGPT citations"},
        ],
        "content_gaps": ["No pricing page", "No about page"],
        "next_30_day_plan": [
            "week1: Add FAQ schema to all top pages",
            "week2: Write 3 long-form articles",
            "week3: Build internal links",
            "week4: Monitor and iterate",
        ],
    },
}


@pytest.fixture
def _seed_report():
    """Put a known report into current_analysis so build_*_report can use it."""
    analyzer.current_analysis = SAMPLE_REPORT
    yield
    analyzer.current_analysis = {}


def test_excel_returns_attachment(_seed_report):
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/excel")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers.get("Content-Type", "")
    cd = r.headers.get("Content-Disposition", "")
    assert "attachment" in cd
    assert ".xlsx" in cd


def test_excel_404_when_no_report():
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/excel")
    assert r.status_code == 404


def test_pdf_returns_attachment(_seed_report):
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/pdf")
    assert r.status_code == 200
    assert r.headers.get("Content-Type") == "application/pdf"
    cd = r.headers.get("Content-Disposition", "")
    assert "attachment" in cd
    assert ".pdf" in cd


def test_pdf_404_when_no_report():
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/pdf")
    assert r.status_code == 404


def test_excel_workbook_actually_built(_seed_report):
    """Open the bytes and confirm openpyxl can read 4 sheets back."""
    import openpyxl

    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/excel")
    assert r.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(r.data), data_only=True)
    assert set(wb.sheetnames) == {
        "AEO Summary", "Competitors", "FAQs & Recommendations", "30-Day Plan"
    }


def test_pdf_starts_with_magic_header(_seed_report):
    """A real PDF always begins with %PDF-"""
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get("/api/download/pdf")
    assert r.status_code == 200
    assert r.data[:5] == b"%PDF-"
