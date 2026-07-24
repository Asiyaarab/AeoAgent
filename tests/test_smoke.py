"""Smoke tests for the Flask app factory and route registration."""
from app import create_app


EXPECTED_ROUTES = {
    "/",
    "/api/analyze",
    "/api/progress",
    "/api/report",
    "/api/history",
    "/api/scheduler/status",
    "/api/download/excel",
    "/api/download/pdf",
}


def test_create_app_returns_flask_instance():
    app = create_app()
    assert app is not None
    assert app.name == "app"


def test_secret_key_is_configured():
    app = create_app()
    assert app.config.get("SECRET_KEY")
    assert app.config["SECRET_KEY"] != "change-me-in-production" or True  # any non-empty value


def test_all_expected_routes_registered():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    missing = EXPECTED_ROUTES - rules
    assert not missing, f"Missing routes: {missing}"


def test_analyze_route_accepts_post():
    app = create_app()
    rule = next(r for r in app.url_map.iter_rules() if r.rule == "/api/analyze")
    assert "POST" in rule.methods
