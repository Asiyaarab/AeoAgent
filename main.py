"""
AEO Agent — entry point.

Run with:
    python main.py

Environment variables (load from .env):
    SCRAPFLY_API_KEY     — required (https://scrapfly.io)
    Z_AI_API_KEY         — required (https://open.bigmodel.cn)
    FLASK_HOST           — default 0.0.0.0
    FLASK_PORT           — default 5000
    FLASK_DEBUG          — default false
    SECRET_KEY           — Flask secret (change in production)
"""
from app import create_app
from app.config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT, get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    app = create_app()
    logger.info("Starting AEO Agent on http://%s:%d", FLASK_HOST, FLASK_PORT)
    # use_reloader=False so APScheduler doesn't double-fire
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)
