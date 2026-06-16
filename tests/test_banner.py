"""Tests for the PGLU banner (pure)."""

from __future__ import annotations

from sitedoctor.banner import render_banner


def test_banner_contains_brand_text():
    out = render_banner(color=False, unicode_ok=True)
    assert "PGLU" in out
    assert "site-doctor" in out


def test_banner_unicode_uses_block_chars():
    out = render_banner(color=False, unicode_ok=True)
    assert "█" in out


def test_banner_ascii_fallback_is_pure_ascii():
    out = render_banner(color=False, unicode_ok=False)
    out.encode("ascii")  # must not raise
    assert "PGLU" in out


def test_banner_no_color_has_no_escape_codes():
    out = render_banner(color=False, unicode_ok=False)
    assert "\033" not in out


def test_banner_color_adds_escape_codes():
    out = render_banner(color=True, unicode_ok=True)
    assert "\033" in out
