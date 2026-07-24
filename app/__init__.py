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

from .config import (
    FLASK_DEBUG,
    SECRET_KEY,
    TEMPLATES_DIR,
    get_logger,
)
from .routes import api
from .scheduler import init_scheduler

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
    app.register_blueprint(api)

    # Start the background scheduler exactly once
    init_scheduler()
    logger.info("AEO Agent app created and ready")
    return app
