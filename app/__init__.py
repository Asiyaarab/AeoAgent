"""
Flask application factory.

Usage:
    from app import create_app
    app = create_app()
    app.run(...)

Why a factory? It makes the app:
  - importable without side effects (no module-level scheduler start)
  - easy to test (override config, swap out dependencies)
  - safe under WSGI reloaders
"""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .config import (
    FLASK_DEBUG,
    SECRET_KEY,
    TEMPLATES_DIR,
    get_logger,
)
from .routes import api
from .scheduler import init_scheduler
from .version import __version__

__all__ = ["create_app", "__version__"]

logger = get_logger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask app, registering the blueprint + scheduler."""
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=None,  # all assets are inlined in dashboard.html
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request cap
    app.config["VERSION"] = __version__

    # Permissive CORS by default — tighten via CORS_ORIGINS env var in production
    cors_origins = _parse_cors_origins()
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    app.register_blueprint(api)

    # Start the background scheduler exactly once
    init_scheduler()
    logger.info("AEO Agent v%s ready", __version__)
    return app


def _parse_cors_origins() -> list[str] | str:
    """Return a list of allowed CORS origins, or '*' for everything."""
    import os

    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if raw in ("", "*"):
        return "*"
    return [o.strip() for o in raw.split(",") if o.strip()]
