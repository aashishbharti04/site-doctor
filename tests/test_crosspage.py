"""Tests for cross-page (site-wide) findings and CSV export (pure)."""

from __future__ import annotations

import csv

from sitedoctor.checks import Finding
from sitedoctor.links import LinkResult
from sitedoctor.parser import PageData
from sitedoctor.report import PageReport, SiteReport, _cross_page_findings
from sitedoctor.reporters import write_csv


def test_duplicate_title_detected():
    pages = [
        PageData(url="https://e.com/a", title="Home", meta={"description": "x"}),
        PageData(url="https://e.com/b", title="Home", meta={"description": "y"}),
    ]
    codes = {f.code for f in _cross_page_findings(pages)}
    assert "duplicate-title" in codes


def test_duplicate_meta_detected():
    pages = [
        PageData(url="https://e.com/a", title="A", meta={"description": "same"}),
        PageData(url="https://e.com/b", title="B", meta={"description": "same"}),
    ]
    codes = {f.code for f in _cross_page_findings(pages)}
    assert "duplicate-meta-desc" in codes


def test_unique_titles_no_findings():
    pages = [
        PageData(url="https://e.com/a", title="A", meta={"description": "one"}),
        PageData(url="https://e.com/b", title="B", meta={"description": "two"}),
    ]
    assert _cross_page_findings(pages) == []


def test_write_csv(tmp_path):
    r = SiteReport(start_url="https://e.com")
    r.pages = [PageReport("https://e.com", {"seo": 90, "a11y": 90, "performance": 90},
                          [Finding("seo", "warn", "title-long", "Title too long.")])]
    r.broken_links = [LinkResult("https://e.com/x", 404, "broken", "HTTP 404")]
    r.unverified_links = [LinkResult("https://linkedin.com/in/x", 999, "blocked", "HTTP 999")]
    out = tmp_path / "report.csv"
    write_csv(r, str(out))

    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows[0] == ["type", "page_or_url", "category", "severity", "code", "message"]
    types = {row[0] for row in rows[1:]}
    assert {"issue", "broken-link", "unverified-link"} <= types
