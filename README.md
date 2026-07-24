# 🧠 AEO Agent — AI Engine Optimization Bot

> **Analyze any website's visibility on ChatGPT, Gemini & Google AI Overview in under a minute.**

AEO Agent scrapes your site (and up to 4 competitors) through **Scrapfly**, scores your visibility on each AI engine with **Z.ai**, then generates:

- 📊 Per-platform AEO scores (0–100) with a colour-coded breakdown
- 🕵️ Competitor intelligence — what they do better, where you can outrank them
- 💡 5 trending FAQs to add to your site (platform-targeted)
- 🎯 5 strategic recommendations (HIGH / MEDIUM / LOW priority)
- 📅 A 30-day action plan, week by week
- 📥 Downloadable **Excel** (4 sheets) and **PDF** (branded) reports

> **Bonus:** Auto-runs on the **1st, 15th, and 30th of every month at 02:00 UTC** via APScheduler — set the URL once, get fresh reports for free.

![Auto-runs](https://img.shields.io/badge/Auto--runs-1st%20%C2%B7%2015th%20%C2%B7%2030th-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
[![CI](https://github.com/Asiyaarab/AeoAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/Asiyaarab/AeoAgent/actions/workflows/ci.yml)

---

## 📸 Screenshots

Dashboard preview:

| | |
| --- | --- |
| ![Dashboard 1](assets/dashboard1.png.png) | ![Dashboard 2](assets/dashboard2.png.png) |
| ![Dashboard 3](assets/dashboard3.png.png) | ![Dashboard 4](assets/dashboard4.png.png) |

---

## ✨ Features

- 🌐 **Real website scraping** via Scrapfly — bypasses Cloudflare, executes JS, handles SPA sites
- 🤖 **AI-powered scoring** via Z.ai (OpenAI-compatible) — different scoring rules per platform
- 🕵️ **Competitor detection** — AI identifies 4 direct competitors automatically
- ⚔️ **Head-to-head analysis** — strengths, weaknesses, opportunities per competitor
- ❓ **FAQ generator** — 5 trending FAQs tailored to ChatGPT / Gemini / Both
- 📋 **30-day action plan** — week-by-week tactical recommendations
- ⏰ **Scheduled runs** — auto-reports on the 1st, 15th, 30th at 02:00 UTC
- 📊 **Excel export** — 4-sheet workbook with brand styling
- 📄 **PDF export** — A4 layout, colour-coded scores, copy-paste ready
- 🔌 **REST API** — 7 endpoints for programmatic access
- 💾 **CSV history** — every run appended to `data/analysis_history.csv`
- 📁 **JSON archives** — full reports saved to `reports/report_<id>.json`

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Browser (UI)                         │
│                  app/templates/dashboard.html               │
└────────────────────────────┬─────────────────────────────────┘
                             │ JSON / Fetch
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       Flask app (main.py)                    │
│                                                               │
│  app/routes.py  ── 7 endpoints (/, /api/*, /download/*)      │
│                                                               │
│  app/analyzer.py  ── pipeline orchestrator (5 stages)        │
│       │                                                       │
│       ├─► app/scraper.py  ── Scrapfly  (Cloudflare bypass)   │
│       ├─► app/ai_client.py ── Z.ai  (OpenAI-compatible)      │
│       └─► app/reports.py  ── openpyxl + reportlab            │
│                                                               │
│  app/scheduler.py  ── APScheduler  (1st/15th/30th @ 02:00)  │
│  app/config.py     ── env, paths, constants                  │
│  app/utils.py      ── JSON parsing, URL helpers              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │ data/   logs/  reports/│
                └────────────────────────┘
```

### Pipeline (5 stages)

| # | Stage | What happens |
| --- | --- | --- |
| 1 | **Scrape** | Fetch main site HTML through Scrapfly, extract meta/headings/schema/FAQs |
| 2 | **Competitors** | Ask Z.ai for 4 direct competitor URLs |
| 3 | **AEO Score** | Ask Z.ai for per-platform scores + strengths/weaknesses/quick-wins |
| 4 | **Compare** | Scrape + analyze each competitor head-to-head |
| 5 | **Insights** | Ask Z.ai for FAQs and a 30-day action plan |

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Web framework | Flask 3.0 |
| Scraping | Scrapfly API (handles Cloudflare / JS / bot detection) |
| AI | Z.ai (OpenAI-compatible) — model: `glm-4.5-flash` |
| Scheduling | APScheduler 3.10 (BackgroundScheduler + CronTrigger) |
| Reports | openpyxl 3.1 (Excel) + reportlab 4.2 (PDF) |
| Config | python-dotenv |
| Language | Python 3.10+ |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Asiyaarab/AeoAgent.git
cd AeoAgent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
# edit .env and fill in:
#   SCRAPFLY_API_KEY=...
#   Z_AI_API_KEY=...
```

Get keys from:
- **Scrapfly** → https://scrapfly.io/ (free trial credits)
- **Z.ai** → https://open.bigmodel.cn/ (sign up → API keys)

### 3. Run

```bash
python main.py
```

Open **http://localhost:5000** in your browser, type a website, and watch the progress bar.

---

## ⚙️ Configuration

All settings live in `app/config.py` and can be overridden via `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SCRAPFLY_API_KEY` | — | **Required.** Scrapfly account key |
| `Z_AI_API_KEY` | — | **Required.** Z.ai account key |
| `Z_AI_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | Override if you proxy Z.ai |
| `Z_AI_MODEL` | `glm-4.5-flash` | Swap model (e.g. `glm-4-plus`) |
| `FLASK_HOST` | `0.0.0.0` | Bind interface |
| `FLASK_PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `false` | Flask debug mode |
| `SECRET_KEY` | `change-me-...` | Flask session secret |
| `LOG_LEVEL` | `INFO` | Python log level |

---

## 🔌 API Reference

Base URL: `http://localhost:5000`

### `GET /`
Renders the single-page dashboard (HTML/JS frontend).

### `POST /api/analyze`
Kick off a new analysis. Returns immediately; poll `/api/progress`.

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Response:**
```json
{ "status": "started", "url": "https://example.com" }
```

### `GET /api/progress`
Stream live progress for the current run.

```json
{ "status": "running", "progress": "Analyzing 4 competitors...", "progress_pct": 65, "run_id": "20260116_102430" }
```

### `GET /api/report`
Fetch the full completed report (only when `status == "success"`).

### `GET /api/history`
Last 30 runs (in-memory).

### `GET /api/scheduler/status`
```json
{
  "running": true,
  "next_run": "2026-07-30T02:00:00+00:00",
  "schedule": "1st, 15th, 30th at 02:00 UTC",
  "configured_url": "https://example.com"
}
```

### `GET /api/download/excel`
Streams a styled 4-sheet `.xlsx` (AEO Summary, Competitors, FAQs & Recs, 30-Day Plan).

### `GET /api/download/pdf`
Streams a branded A4 `.pdf` report.

---

## 📁 Project Structure

```
AeoAgent/
├── app/                          # All application code
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Env vars, paths, constants
│   ├── utils.py                  # JSON / URL / time helpers
│   ├── scraper.py                # Scrapfly integration
│   ├── ai_client.py              # Z.ai wrapper
│   ├── analyzer.py               # 5-stage AEO pipeline
│   ├── reports.py                # Excel + PDF generation
│   ├── scheduler.py              # APScheduler setup
│   ├── routes.py                 # Flask endpoints
│   └── templates/
│       └── dashboard.html        # Single-page UI
├── data/                         # auto-created (gitignored)
├── logs/                         # auto-created (gitignored)
├── reports/                      # auto-created (gitignored)
├── main.py                       # Thin entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile                      # Heroku / Render deployment
├── runtime.txt                   # Python version pin
├── LICENSE
└── README.md
```

---

## 🗓️ Scheduled Runs

The scheduler is started inside `create_app()` and runs in the background.

- **Trigger:** Cron, day `1,15,30`, hour `2`, minute `0`, timezone `UTC`
- **Target URL:** the most recent URL submitted via `/api/analyze`
- **Output:** saved JSON in `reports/`, CSV row in `data/analysis_history.csv`, last 30 kept in memory for `/api/history`
- **Disable:** remove the `init_scheduler()` call in `app/__init__.py`
- **Override schedule:** edit `SCHEDULER_*` constants in `app/config.py`

> ⚠️ Scheduled runs only fire while the Flask process is running. For 24/7 scheduling, deploy to Render / Railway / Fly.io (see below).

---

## ☁️ Deployment

### Render (recommended — free tier)

1. Push this repo to GitHub
2. On Render → **New** → **Web Service** → connect the repo
3. Render auto-detects `Procfile` and `runtime.txt`
4. Set environment variables in Render dashboard:
   - `SCRAPFLY_API_KEY`
   - `Z_AI_API_KEY`
   - `SECRET_KEY` (any long random string)
5. Deploy. Your app will be live at `https://<name>.onrender.com`.

### Railway

```bash
railway init
railway variables set SCRAPFLY_API_KEY=... Z_AI_API_KEY=...
railway up
```

### Local (development)

```bash
python main.py
# → http://localhost:5000
```

---

## 🧪 Smoke Test (without API keys)

```bash
python -c "from app import create_app; app = create_app(); print('App created OK:', app)"
```

Expected: `App created OK: <Flask 'app'>`

---

## ✅ Tests

A small pytest suite (20 tests across 3 files) covers config loading,
URL/JSON/timestamp helpers, and the Flask app factory. CI runs the
suite on every push and PR across Python 3.10, 3.11, and 3.12.

### Run locally

```bash
pip install -r requirements-dev.txt
pytest
```

### What's covered

| File | What it asserts |
| --- | --- |
| `tests/test_config.py` | `BASE_DIR`/`DATA_DIR`/`LOG_DIR`/`REPORT_DIR` are `Path` objects, directories are auto-created, default `FLASK_HOST`/`FLASK_PORT`/`SECRET_KEY`, external endpoints use HTTPS, `Z_AI_MODEL` is non-empty. |
| `tests/test_utils.py` | `normalize_url` adds `https://` only when needed, `extract_domain` strips path/scheme and handles empty input, `parse_json` handles plain JSON + markdown fences, `safe_extract_json_array` finds the first list and returns `[]` when none exists, `now_compact` format, `date_only` slice. |
| `tests/test_smoke.py` | `create_app()` returns a Flask instance, `SECRET_KEY` is set, all 8 expected routes are registered, `POST` is allowed on `/api/analyze`. |

CI status: see the badge at the top of this README.

---

## 🐛 Troubleshooting

| Problem | Fix |
| --- | --- |
| `SCRAPFLY_API_KEY missing from .env` | Create `.env` (copy from `.env.example`) and add your key |
| `Z.ai API status: 401` | Wrong/expired Z.ai key. Generate a new one at open.bigmodel.cn |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |
| Scheduler doesn't fire | Make sure the Flask process is running at 02:00 UTC. For 24/7 use, deploy. |
| Empty dashboard | Check browser console — likely CORS. Access via `http://localhost:5000`, not `file://` |
| PDF download fails | `pip install reportlab --upgrade` (needs ≥ 4.0) |

---

## 🗺️ Roadmap

- [ ] Persist history in SQLite instead of memory
- [ ] Email the PDF report automatically on scheduled runs
- [ ] Add a `/api/compare?urls=a.com,b.com` endpoint
- [ ] Multi-language support (Hindi / Spanish / French reports)
- [ ] Replace Z.ai with a swappable provider (OpenAI, Anthropic, local Llama)
- [ ] User accounts + per-domain tracking over time
- [ ] Webhook notifications when scores drop

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

## 🙋‍♀️ Maintainer

**Asiya Arab**
- GitHub: [@Asiyaarab](https://github.com/Asiyaarab)
- Project: [github.com/Asiyaarab/AeoAgent](https://github.com/Asiyaarab/AeoAgent)

Built with ❤️ for the AEO / GEO community.
