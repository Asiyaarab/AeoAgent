# Changelog

All notable changes to AEO Agent are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-07-29

### Added
- `GET /api/health` — liveness probe for Docker / k8s / load balancers
- `GET /api/version` — returns the running AEO Agent version
- `GET/POST /api/compare?urls=a.com,b.com` — head-to-head URL comparison
  (was on the roadmap; now implemented)
- In-memory TTL cache (`app/cache.py`) so the same URL isn't re-analyzed
  within `CACHE_TTL_SECONDS` (default 600 s)
- CORS support via `flask-cors` (configurable via `CORS_ORIGINS` env var)
- Strict URL validation on `/api/analyze` and `/api/compare` (rejects
  malformed input with a 400 instead of failing deep in the pipeline)
- `Dockerfile` + `docker-compose.yml` + `.dockerignore` for one-command
  containerized deployment
- `Makefile` with `install`, `test`, `test-cov`, `lint`, `format`,
  `typecheck`, `smoke`, `run`, `docker-build`, `docker-run`, `clean` targets
- `.pre-commit-config.yaml` (ruff + black + standard hooks)
- `pyproject.toml` with project metadata + tool configs (ruff, black, mypy, pytest)
- `CONTRIBUTING.md` and `SECURITY.md`
- Expanded test suite — **20 → 80+ tests** covering `analyzer`, `scraper`,
  `ai_client`, `reports`, `scheduler`, `cache`, `version`, and the Flask routes

### Changed
- `app/__init__.py` now exports `__version__` and enables CORS on `/api/*`
- `app/scraper.py` schema parser now correctly handles a list of JSON-LD
  objects (was only treating the first dict) and uses the `json` module
  directly instead of `__import__("json")`
- `app/requirements.txt` adds `flask-cors==4.0.1`
- `app/analyzer.py` short-circuits to a cached report on repeat requests

### Fixed
- `app/scraper.py` now handles a list-typed JSON-LD payload (e.g.
  `[{"@type": "Article"}, {"@type": "WebSite"}]`) and returns sorted,
  deduplicated schema types

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
