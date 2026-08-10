"""Tests for app/scraper.py — HTML signal extraction (no network calls)."""
import pytest

from app.scraper import _parse_html

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Test Co — best widgets in town</title>
  <meta name="description" content="We sell the best widgets online.">
  <meta property="og:title" content="Test Co">
  <link rel="canonical" href="https://test.example.com/">
  <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Organization", "name": "Test Co"}
  </script>
  <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "FAQPage",
     "mainEntity": [{"@type": "Question", "name": "Q1"}]}
  </script>
</head>
<body>
  <h1>Welcome to Test Co</h1>
  <h2>Our Products</h2>
  <h3>Widgets</h3>
  <nav><a href="/about">About</a></nav>
  <section class="faq">
    <h4>What is a widget?</h4>
    <p>A widget is a small useful thing.</p>
  </section>
  <section class="faq-question">
    <h4>How do I order?</h4>
    <p>Click buy and pay.</p>
  </section>
  <a href="https://test.example.com/contact">Contact us</a>
  <a href="https://external.com/x">External</a>
  <img src="/logo.png" alt="logo">
  <img src="/banner.jpg">
  <script>console.log('noise')</script>
  <style>body { color: red }</style>
</body>
</html>
"""


def test_parse_html_extracts_title_and_meta():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert data["title"] == "Test Co — best widgets in town"
    assert data["meta_desc"] == "We sell the best widgets online."
    assert data["og_title"] == "Test Co"
    assert data["canonical"] == "https://test.example.com/"


def test_parse_html_extracts_headings_capped():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert data["headings"]["h1"] == ["Welcome to Test Co"]
    assert "Our Products" in data["headings"]["h2"]
    assert "Widgets" in data["headings"]["h3"]


def test_parse_html_extracts_schema_types_sorted():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert data["schema_types"] == ["FAQPage", "Organization"]


def test_parse_html_extracts_faqs_from_class_patterns():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert len(data["faqs_found"]) == 2
    assert data["faqs_found"][0]["q"] == "What is a widget?"


def test_parse_html_counts_internal_links_and_images():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    # /about lives inside <nav> which the scraper strips, so only /contact counts.
    # external.com/x is excluded.  →  1 internal link.
    assert data["internal_links"] == 1
    assert data["imgs_total"] == 2
    assert data["imgs_with_alt"] == 1


def test_parse_html_strips_noise_tags_from_body():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert "console.log" not in data["body_text"]
    assert "color: red" not in data["body_text"]
    assert "Welcome to Test Co" in data["body_text"]


def test_parse_html_returns_status_ok():
    data = _parse_html("https://test.example.com/", SAMPLE_HTML)
    assert data["status"] == "ok"
    assert "scraped_at" in data


def test_parse_html_handles_missing_title_and_meta():
    data = _parse_html("https://blank.example.com/", "<html><body>hi</body></html>")
    assert data["title"] == ""
    assert data["meta_desc"] == ""
    assert data["schema_types"] == []
    assert data["faqs_found"] == []


def test_parse_html_handles_invalid_json_ld_gracefully():
    html = """
    <html><head>
      <title>x</title>
      <script type="application/ld+json">this is not json</script>
      <script type="application/ld+json">["not", "a", "dict"]</script>
      <script type="application/ld+json">{"@type": "WebSite"}</script>
    </head><body></body></html>
    """
    data = _parse_html("https://x.example.com/", html)
    # bad JSON skipped, list-typed JSON-LD is ignored, only the dict counts
    assert data["schema_types"] == ["WebSite"]


def test_parse_html_accepts_list_of_json_ld_objects():
    html = """
    <html><head>
      <title>x</title>
      <script type="application/ld+json">
        [{"@type": "Article"}, {"@type": "BreadcrumbList"}]
      </script>
    </head><body></body></html>
    """
    data = _parse_html("https://x.example.com/", html)
    assert sorted(data["schema_types"]) == ["Article", "BreadcrumbList"]
