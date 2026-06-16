"""Audit rules. Each function takes a PageData and returns a list of Findings.

All pure — no network, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .parser import PageData

SEVERITIES = ("error", "warn", "info")


@dataclass
class Finding:
    category: str           # "seo" | "a11y" | "performance"
    severity: str           # "error" | "warn" | "info"
    code: str               # short machine code
    message: str            # human message


# ---------------------------------------------------------------------------
# SEO
# ---------------------------------------------------------------------------
def seo_checks(p: PageData) -> list[Finding]:
    f: list[Finding] = []
    add = lambda s, c, m: f.append(Finding("seo", s, c, m))

    title = (p.title or "").strip()
    if not title:
        add("error", "title-missing", "Missing <title> tag.")
    elif len(title) < 10:
        add("warn", "title-short", f"Title is very short ({len(title)} chars).")
    elif len(title) > 60:
        add("warn", "title-long", f"Title is {len(title)} chars; >60 may be truncated in SERPs.")

    desc = p.meta.get("description", "").strip()
    if not desc:
        add("error", "meta-desc-missing", "Missing meta description.")
    elif len(desc) < 50:
        add("warn", "meta-desc-short", f"Meta description is short ({len(desc)} chars).")
    elif len(desc) > 160:
        add("warn", "meta-desc-long", f"Meta description is {len(desc)} chars (>160).")

    if len(p.h1) == 0:
        add("error", "h1-missing", "No <h1> heading on the page.")
    elif len(p.h1) > 1:
        add("warn", "h1-multiple", f"Multiple <h1> tags ({len(p.h1)}); use exactly one.")

    if not p.canonical:
        add("warn", "canonical-missing", "No canonical link; risks duplicate-content issues.")

    if not any(k.startswith("og:") for k in p.meta):
        add("warn", "og-missing", "No Open Graph tags; poor social sharing previews.")

    if not p.meta.get("viewport"):
        add("warn", "viewport-missing", "No viewport meta; not mobile-friendly.")

    if "noindex" in p.meta.get("robots", "").lower():
        add("info", "robots-noindex", "Page is set to noindex.")

    if not p.has_jsonld:
        add("info", "jsonld-missing", "No JSON-LD structured data found.")

    if p.word_count < 100:
        add("warn", "thin-content", f"Thin content (~{p.word_count} words).")

    return f


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
_BAD_LINK_TEXT = {"click here", "here", "read more", "more", "link", "this"}


def a11y_checks(p: PageData) -> list[Finding]:
    f: list[Finding] = []
    add = lambda s, c, m: f.append(Finding("a11y", s, c, m))

    if not p.lang:
        add("error", "html-lang-missing", "No lang attribute on <html>.")

    missing_alt = [im for im in p.images if im.alt is None]
    if missing_alt:
        add("error", "img-alt-missing",
            f"{len(missing_alt)}/{len(p.images)} images missing an alt attribute.")
    empty_alt = [im for im in p.images if im.alt == "" ]
    if len(empty_alt) > 0 and len(empty_alt) == len(p.images) and p.images:
        add("warn", "img-alt-empty", "All images have empty alt text.")

    if not (p.title or "").strip():
        add("error", "doc-title-missing", "No document <title> (screen-reader landmark).")

    bad = [l for l in p.links if l.text.strip().lower() in _BAD_LINK_TEXT]
    if bad:
        add("warn", "link-text-vague",
            f"{len(bad)} links use vague text like 'click here' / 'read more'.")

    empty_links = [l for l in p.links if not l.text.strip()]
    if empty_links:
        add("warn", "link-text-empty", f"{len(empty_links)} links have no text.")

    if p.inputs_without_label > 0:
        add("error", "input-no-label",
            f"{p.inputs_without_label}/{p.total_inputs} form fields lack an accessible label.")

    # heading hierarchy: levels shouldn't jump by more than 1
    levels = [lvl for lvl, _ in p.headings]
    for prev, cur in zip(levels, levels[1:]):
        if cur - prev > 1:
            add("warn", "heading-skip",
                f"Heading level jumps from h{prev} to h{cur}.")
            break

    return f


# ---------------------------------------------------------------------------
# Performance (heuristic, from HTML only)
# ---------------------------------------------------------------------------
def performance_checks(p: PageData) -> list[Finding]:
    f: list[Finding] = []
    add = lambda s, c, m: f.append(Finding("performance", s, c, m))

    kb = p.html_bytes / 1024
    if kb > 200:
        add("error", "html-huge", f"HTML document is large ({kb:.0f} KB).")
    elif kb > 100:
        add("warn", "html-large", f"HTML document is {kb:.0f} KB; consider trimming.")

    if p.script_count > 15:
        add("warn", "many-scripts", f"{p.script_count} external scripts; bundle to reduce requests.")

    if p.stylesheet_count > 5:
        add("warn", "many-styles", f"{p.stylesheet_count} stylesheets; consider combining.")

    if p.inline_script_bytes > 50_000:
        add("warn", "inline-js-large",
            f"{p.inline_script_bytes/1024:.0f} KB of inline JS; move to cached files.")

    if len(p.images) > 30:
        add("info", "many-images", f"{len(p.images)} images; ensure lazy-loading & compression.")

    # real measured load time (from the crawler), when available
    if p.load_ms > 4000:
        add("error", "slow-response", f"Slow response ({p.load_ms/1000:.1f}s to load).")
    elif p.load_ms > 2000:
        add("warn", "slow-response", f"Response took {p.load_ms/1000:.1f}s; aim for < 2s.")

    return f


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
def security_checks(p: PageData) -> list[Finding]:
    f: list[Finding] = []
    add = lambda s, c, m: f.append(Finding("security", s, c, m))

    if p.final_url and not p.is_https:
        add("error", "no-https", "Page is served over HTTP, not HTTPS.")

    # mixed content: absolute http:// sub-resources on an https page
    if p.is_https:
        mixed = [u for u in p.resource_urls if u.startswith("http://")]
        if mixed:
            add("error", "mixed-content",
                f"{len(mixed)} sub-resource(s) loaded over insecure HTTP.")

    # security headers (only meaningful when we actually fetched the page)
    h = p.headers
    if h:
        if p.is_https and "strict-transport-security" not in h:
            add("warn", "hsts-missing", "Missing Strict-Transport-Security (HSTS) header.")
        if "content-security-policy" not in h:
            add("warn", "csp-missing", "Missing Content-Security-Policy header.")
        if "x-content-type-options" not in h:
            add("warn", "xcto-missing", "Missing X-Content-Type-Options: nosniff header.")
        if "x-frame-options" not in h and "content-security-policy" not in h:
            add("warn", "xfo-missing", "Missing X-Frame-Options (clickjacking protection).")
        if "referrer-policy" not in h:
            add("info", "referrer-missing", "Missing Referrer-Policy header.")

    return f


def run_all(p: PageData) -> list[Finding]:
    return seo_checks(p) + a11y_checks(p) + performance_checks(p) + security_checks(p)
