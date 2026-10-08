"""
AEO Agent — entry point.

Run locally with:
    python main.py
"""

from app import create_app
from app.config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT, get_logger

logger = get_logger(__name__)

# Create the Flask application at module level.
# Required for Vercel deployment.
app = create_app()


if __name__ == "__main__":
    logger.info(
        "Starting AEO Agent on http://%s:%d",
        FLASK_HOST,
        FLASK_PORT,
    )

    # use_reloader=False so APScheduler doesn't double-fire
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False,
    )
