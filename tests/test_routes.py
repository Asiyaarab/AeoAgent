"""Smoke tests for the Flask app factory and route registration."""
from app import create_app
from app.version import __version__


EXPECTED_ROUTES = {
    "/",
    "/api/analyze",
    "/api/progress",
    "/api/report",
    "/api/history",
    "/api/scheduler/status",
    "/api/download/excel",
    "/api/download/pdf",
    "/api/health",
    "/api/version",
    "/api/compare",
}


def test_create_app_returns_flask_instance():
    app = create_app()
    assert app is not None
    assert app.name == "app"


def test_secret_key_is_configured():
    app = create_app()
    assert app.config.get("SECRET_KEY")


def test_all_expected_routes_registered():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    missing = EXPECTED_ROUTES - rules
    assert not missing, f"Missing routes: {missing}"


def test_analyze_route_accepts_post():
    app = create_app()
    rule = next(r for r in app.url_map.iter_rules() if r.rule == "/api/analyze")
    assert "POST" in rule.methods


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert "scheduler_running" in body


def test_version_endpoint():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.get_json()["version"] == __version__


def test_analyze_rejects_missing_url():
    app = create_app()
    client = app.test_client()
    r = client.post("/api/analyze", json={})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_analyze_rejects_malformed_url():
    app = create_app()
    client = app.test_client()
    r = client.post("/api/analyze", json={"url": "not a valid url!!!"})
    assert r.status_code == 400


def test_analyze_accepts_valid_url():
    app = create_app()
    client = app.test_client()
    # We don't have the real pipeline running; just confirm the route accepts
    # a well-formed URL and returns the "started" payload immediately.
    r = client.post("/api/analyze", json={"url": "example.com"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "started"
    assert body["url"] == "https://example.com"


def test_compare_get_with_query_string():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/compare?urls=example.com,github.com")
    assert r.status_code == 200
    body = r.get_json()
    assert body["urls"] == ["https://example.com", "https://github.com"]


def test_compare_rejects_too_few_urls():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/compare?urls=example.com")
    assert r.status_code == 400


def test_compare_rejects_too_many_urls():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/compare?urls=a.com,b.com,c.com,d.com")
    assert r.status_code == 400


def test_compare_rejects_invalid_url():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/compare?urls=example.com,notvalid!!")
    assert r.status_code == 400


def test_compare_post_with_json():
    app = create_app()
    client = app.test_client()
    r = client.post("/api/compare", json={"urls": ["example.com", "github.com"]})
    assert r.status_code == 200


def test_cors_headers_present():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    # flask-cors adds Access-Control-Allow-Origin for matching origins
    assert "Access-Control-Allow-Origin" in r.headers
