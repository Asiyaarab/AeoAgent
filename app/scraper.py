"""
Scrapfly-based web scraper.

Scrapfly is used (instead of raw requests) because it bypasses Cloudflare,
executes JavaScript, and handles bot detection. The scraped page is then
parsed with BeautifulSoup to extract SEO / AEO signals.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import (
    SCRAPFLY_API_KEY,
    SCRAPFLY_BASE_URL,
    SCRAPFLY_DEFAULTS,
    get_logger,
)
from .utils import extract_domain, now_iso, normalize_url

logger = get_logger(__name__)


def scrape_with_scrapfly(url: str) -> str:
    """Fetch a page's HTML through Scrapfly. Returns raw HTML string."""
    if not SCRAPFLY_API_KEY:
        raise RuntimeError("SCRAPFLY_API_KEY missing from .env file")

    params = {"key": SCRAPFLY_API_KEY, "url": url, **SCRAPFLY_DEFAULTS}
    response = requests.get(SCRAPFLY_BASE_URL, params=params, timeout=45)

    if response.status_code != 200:
        raise RuntimeError(
            f"Scrapfly error {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    result = data.get("result", {}) or {}
    if result.get("status_code") not in (200, None):
        raise RuntimeError(f"Target site returned {result.get('status_code')}")

    return result.get("content", "") or ""


def _parse_html(url: str, html: str) -> dict[str, Any]:
    """Extract SEO / AEO signals from a page's HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # ── Meta tags ────────────────────────────────────────────────
    title = soup.find("title")
    description = soup.find("meta", attrs={"name": "description"})
    og_title = soup.find("meta", property="og:title")
    canonical = soup.find("link", rel="canonical")

    # ── Headings ─────────────────────────────────────────────────
    headings = {
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")][:5],
        "h2": [h.get_text(strip=True) for h in soup.find_all("h2")][:10],
        "h3": [h.get_text(strip=True) for h in soup.find_all("h3")][:10],
    }

    # ── FAQ patterns ─────────────────────────────────────────────
    faqs: list[dict[str, str]] = []
    for el in soup.find_all(["details", "div", "section"]):
        cls = " ".join(el.get("class", []) or [])
        if any(k in cls.lower() for k in ("faq", "question", "accordion")):
            q = el.find(["summary", "h3", "h4", "dt"])
            a = el.find(["p", "dd", "div"])
            if q and a:
                faqs.append({
                    "q": q.get_text(strip=True),
                    "a": a.get_text(strip=True)[:200],
                })

    # ── Schema markup ────────────────────────────────────────────
    schemas: list[dict] = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            schemas.append(__import__("json").loads(s.string or "{}"))
        except Exception:
            continue
    schema_types = list({s.get("@type", "") for s in schemas if s.get("@type")})

    # ── Body text (clean) ────────────────────────────────────────
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = " ".join(soup.get_text(" ", strip=True).split())[:3000]

    # ── Link & image stats ───────────────────────────────────────
    domain = extract_domain(url)
    internal_links = len([
        a for a in soup.find_all("a", href=True)
        if domain in (a["href"] or "") or a["href"].startswith("/")
    ])

    imgs = soup.find_all("img")
    imgs_total = len(imgs)
    imgs_alt = len([i for i in imgs if i.get("alt")])

    title_txt = title.get_text(strip=True) if title else "No title"
    logger.info("Scraped OK: '%s' (%d words)", title_txt, len(body_text.split()))

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else "",
        "meta_desc": description.get("content", "") if description else "",
        "og_title": og_title.get("content", "") if og_title else "",
        "canonical": canonical.get("href", "") if canonical else "",
        "headings": headings,
        "faqs_found": faqs[:5],
        "schema_types": schema_types,
        "internal_links": internal_links,
        "imgs_total": imgs_total,
        "imgs_with_alt": imgs_alt,
        "body_text": body_text,
        "word_count": len(body_text.split()),
        "scraped_at": now_iso(),
        "status": "ok",
    }


def scrape_website(url: str) -> dict[str, Any]:
    """Scrape a website using Scrapfly and extract all SEO/AEO signals.

    Returns either a populated dict on success, or a dict with
    ``status="error"`` and an ``error`` key on failure.
    """
    url = normalize_url(url)
    try:
        logger.info("Scraping via Scrapfly: %s", url)
        html = scrape_with_scrapfly(url)
        if not html:
            raise RuntimeError("Empty response from Scrapfly")
        return _parse_html(url, html)
    except Exception as exc:
        logger.error("Scrape failed for %s: %s", url, exc)
        return {"url": url, "status": "error", "error": str(exc)}
