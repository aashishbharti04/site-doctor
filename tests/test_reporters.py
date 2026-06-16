"""Tests for the Markdown / HTML reporters (pure)."""

from __future__ import annotations

from sitedoctor.checks import Finding
from sitedoctor.links import LinkResult
from sitedoctor.report import PageReport, SiteReport
from sitedoctor.reporters import to_html, to_markdown


def sample_report() -> SiteReport:
    findings = [
        Finding("a11y", "error", "img-alt-missing", "2/3 images missing an alt attribute."),
        Finding("seo", "warn", "meta-desc-long", "Meta description is 182 chars (>160)."),
    ]
    r = SiteReport(start_url="https://example.com")
    r.pages = [PageReport("https://example.com",
                          {"seo": 94, "a11y": 85, "performance": 100}, findings)]
    r.scores = {"seo": 94.0, "a11y": 85.0, "performance": 100.0, "links": 50.0}
    r.overall = 84.0
    r.grade = "B — good"
    r.links_checked = 4
    r.broken_links = [LinkResult("https://example.com/missing", 404, False, "HTTP 404")]
    return r


def test_markdown_contains_key_sections():
    md = to_markdown(sample_report())
    assert "# site-doctor report" in md
    assert "Health Score:** 84.0/100" in md
    assert "| SEO | 94.0 |" in md
    assert "img-alt-missing" not in md          # we show the message, not the code
    assert "missing an alt attribute" in md
    assert "404" in md and "https://example.com/missing" in md


def test_html_is_self_contained_and_escaped():
    html = to_html(sample_report())
    assert html.startswith("<!DOCTYPE html>")
    assert "<style>" in html                    # inline CSS, no external deps
    assert "84.0" in html
    assert "https://example.com/missing" in html


def test_html_escapes_dangerous_content():
    r = sample_report()
    r.pages[0].findings.append(
        Finding("seo", "warn", "x", "<script>alert(1)</script>"))
    html = to_html(r)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
