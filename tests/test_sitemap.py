"""Tests for sitemap XML parsing (pure — no network)."""

from __future__ import annotations

from sitedoctor.sitemap import _locs

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/contact</loc></url>
</urlset>
"""

INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-1.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-2.xml</loc></sitemap>
</sitemapindex>
"""


def test_parse_urlset():
    pages, children = _locs(URLSET)
    assert pages == [
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/contact",
    ]
    assert children == []


def test_parse_sitemap_index():
    pages, children = _locs(INDEX)
    assert pages == []
    assert children == [
        "https://example.com/sitemap-1.xml",
        "https://example.com/sitemap-2.xml",
    ]


def test_malformed_xml_is_safe():
    pages, children = _locs("<not xml")
    assert pages == [] and children == []
