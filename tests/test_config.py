"""Tests for app/config.py — paths, directories, defaults."""
from pathlib import Path

from app.config import (
    BASE_DIR,
    DATA_DIR,
    FLASK_HOST,
    FLASK_PORT,
    LOG_DIR,
    REPORT_DIR,
    SCRAPFLY_BASE_URL,
    SECRET_KEY,
    Z_AI_BASE_URL,
    Z_AI_MODEL,
)


def test_paths_are_path_objects():
    assert isinstance(BASE_DIR, Path)
    assert isinstance(DATA_DIR, Path)
    assert isinstance(LOG_DIR, Path)
    assert isinstance(REPORT_DIR, Path)


def test_data_log_report_dirs_created():
    assert DATA_DIR.exists() and DATA_DIR.is_dir()
    assert LOG_DIR.exists() and LOG_DIR.is_dir()
    assert REPORT_DIR.exists() and REPORT_DIR.is_dir()


def test_default_flask_settings():
    assert FLASK_HOST == "0.0.0.0"
    assert FLASK_PORT == 5000
    assert SECRET_KEY  # not empty


def test_external_endpoints_use_https():
    assert SCRAPFLY_BASE_URL.startswith("https://")
    assert Z_AI_BASE_URL.startswith("https://")


def test_zai_model_is_set():
    assert Z_AI_MODEL
    assert isinstance(Z_AI_MODEL, str)
