"""Tests for the audit checks (pure)."""

from __future__ import annotations

from sitedoctor.checks import a11y_checks, performance_checks, seo_checks
from sitedoctor.parser import Image, Link, PageData


def codes(findings):
    return {f.code for f in findings}


def test_seo_flags_missing_essentials():
    p = PageData(url="x")  # empty page
    c = codes(seo_checks(p))
    assert "title-missing" in c
    assert "meta-desc-missing" in c
    assert "h1-missing" in c


def test_seo_clean_page_has_no_errors():
    p = PageData(
        url="x",
        title="A good descriptive page title here",
        meta={"description": "x" * 80, "og:title": "t", "viewport": "width=device-width"},
        canonical="https://e.com/",
        headings=[(1, "Only one h1")],
        has_jsonld=True,
        word_count=300,
    )
    errors = [f for f in seo_checks(p) if f.severity == "error"]
    assert errors == []


def test_seo_multiple_h1_warns():
    p = PageData(url="x", headings=[(1, "a"), (1, "b")])
    assert "h1-multiple" in codes(seo_checks(p))


def test_a11y_missing_alt_and_lang():
    p = PageData(url="x", images=[Image("a.png", None)], lang=None)
    c = codes(a11y_checks(p))
    assert "img-alt-missing" in c
    assert "html-lang-missing" in c


def test_a11y_vague_link_text():
    p = PageData(url="x", lang="en", links=[Link("/a", "click here")])
    assert "link-text-vague" in codes(a11y_checks(p))


def test_a11y_heading_skip():
    p = PageData(url="x", lang="en", headings=[(1, "a"), (4, "b")])
    assert "heading-skip" in codes(a11y_checks(p))


def test_performance_large_html():
    p = PageData(url="x", html_bytes=250 * 1024)
    assert "html-huge" in codes(performance_checks(p))


def test_performance_many_scripts():
    p = PageData(url="x", script_count=20)
    assert "many-scripts" in codes(performance_checks(p))
