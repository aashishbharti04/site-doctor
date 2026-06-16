"""Tests for the pure HTML parser."""

from __future__ import annotations

from sitedoctor.parser import parse_html, same_domain

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Example Page</title>
  <meta name="description" content="A demo page for testing.">
  <meta property="og:title" content="Example">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="/home">
  <link rel="stylesheet" href="/a.css">
  <script type="application/ld+json">{"@type":"WebSite"}</script>
</head>
<body>
  <h1>Main heading</h1>
  <h2>Sub</h2>
  <img src="/a.png" alt="A picture">
  <img src="/b.png">
  <a href="/about">About us</a>
  <a href="https://external.com/x">click here</a>
  <script src="/app.js"></script>
  <p>Some words here for the body text content.</p>
</body>
</html>
"""


def test_basic_fields():
    p = parse_html(HTML, base_url="https://example.com/")
    assert p.title == "Example Page"
    assert p.lang == "en"
    assert p.meta["description"].startswith("A demo")
    assert "og:title" in p.meta
    assert p.meta.get("viewport")
    assert p.canonical == "https://example.com/home"
    assert p.has_jsonld is True
    assert p.stylesheet_count == 1
    assert p.script_count == 1


def test_headings_and_h1():
    p = parse_html(HTML, base_url="https://example.com/")
    assert p.h1 == ["Main heading"]
    assert (2, "Sub") in p.headings


def test_images_alt_detection():
    p = parse_html(HTML, base_url="https://example.com/")
    alts = [im.alt for im in p.images]
    assert "A picture" in alts
    assert None in alts  # the <img> without alt


def test_links_resolved_absolute():
    p = parse_html(HTML, base_url="https://example.com/")
    hrefs = [l.href for l in p.links]
    assert "https://example.com/about" in hrefs
    assert "https://external.com/x" in hrefs


def test_same_domain():
    assert same_domain("https://example.com/x", "https://example.com/")
    assert not same_domain("https://other.com/x", "https://example.com/")


def test_word_count_excludes_script():
    p = parse_html("<html><body><p>one two three</p>"
                   "<script>var x = 'should not count words';</script></body></html>",
                   base_url="https://e.com")
    assert p.word_count == 3
