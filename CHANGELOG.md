# Changelog

All notable changes to AEO Agent are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-07-24

### Added
- Flask 3.0 application factory with a single-page dashboard.
- 5-stage analysis pipeline: scrape → competitors → AEO score → compare → insights.
- Scrapfly-based scraper that extracts SEO/AEO signals (title, meta, headings,
  FAQ patterns, JSON-LD schema types, internal link & image-alt counts).
- Z.ai (OpenAI-compatible) chat client wrapper with JSON-only response parsing.
- Excel (4-sheet) and branded PDF report generators via openpyxl + reportlab.
- APScheduler-driven background job that re-runs the analysis on the 1st, 15th,
  and 30th of each month at 02:00 UTC.
- 7-endpoint REST API: `/api/analyze`, `/api/progress`, `/api/report`,
  `/api/history`, `/api/scheduler/status`, `/api/download/excel`,
  `/api/download/pdf`.
- Single-page dashboard with live progress polling and report download.
- pytest suite (20 tests) covering config loading, URL/JSON/timestamp
  helpers, and the Flask app factory.
- GitHub Actions CI matrix across Python 3.10, 3.11, and 3.12.
- Render + Railway deployment guides.
