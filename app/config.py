"""
Configuration module — loads environment variables, defines constants and paths.

Centralizes all configuration so the rest of the app stays environment-agnostic.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

import os

# Load .env before reading any os.getenv
load_dotenv()

# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
LOG_DIR: Path = BASE_DIR / "logs"
REPORT_DIR: Path = BASE_DIR / "reports"
TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

for _d in (DATA_DIR, LOG_DIR, REPORT_DIR):
    _d.mkdir(exist_ok=True)

# ── API Keys ────────────────────────────────────────────────────────────
SCRAPFLY_API_KEY: str | None = os.getenv("SCRAPFLY_API_KEY")
Z_AI_API_KEY: str | None = os.getenv("Z_AI_API_KEY")

# ── External service endpoints ─────────────────────────────────────────
SCRAPFLY_BASE_URL: str = "https://api.scrapfly.io/scrape"
Z_AI_BASE_URL: str = os.getenv("Z_AI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
Z_AI_MODEL: str = os.getenv("Z_AI_MODEL", "glm-4.5-flash")

# ── Scrapfly parameters ────────────────────────────────────────────────
SCRAPFLY_DEFAULTS: dict = {
    "render_js": "true",   # execute JavaScript (SPA sites)
    "asp": "true",         # anti-scraping protection bypass
    "country": "in",       # India — good for Myntra, Flipkart etc.
    "retry": "3",
    "timeout": "30000",
}

# ── Scheduler ───────────────────────────────────────────────────────────
SCHEDULER_TRIGGER: str = "cron"
SCHEDULER_DAY: str = "1,15,30"   # 1st, 15th, 30th of month
SCHEDULER_HOUR: int = 2
SCHEDULER_MINUTE: int = 0
SCHEDULER_TIMEZONE: str = "UTC"

# ── App ────────────────────────────────────────────────────────────────
FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

# ── Logging ────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
LOG_FILE: Path = LOG_DIR / "aeo_agent.log"


def configure_logging() -> None:
    """Initialize root logger with file + console handlers (idempotent)."""
    root = logging.getLogger()
    if root.handlers:                       # already configured
        return

    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with the shared configuration."""
    configure_logging()
    return logging.getLogger(name)


# ── Startup diagnostics ────────────────────────────────────────────────
logger = get_logger(__name__)
logger.info("Scrapfly key: %s", "YES" if SCRAPFLY_API_KEY else "MISSING - check .env")
logger.info("Z.ai key:     %s", "YES" if Z_AI_API_KEY else "MISSING - check .env")
