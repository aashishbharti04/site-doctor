"""Tests for the security checks and JUnit export (pure)."""

from __future__ import annotations

from sitedoctor.checks import security_checks
from sitedoctor.parser import PageData


def codes(findings):
    return {f.code for f in findings}


def test_http_page_flagged():
    p = PageData(url="http://e.com", final_url="http://e.com", is_https=False)
    assert "no-https" in codes(security_checks(p))


def test_missing_security_headers_flagged():
    p = PageData(url="https://e.com", final_url="https://e.com", is_https=True,
                 headers={"content-type": "text/html"})
    c = codes(security_checks(p))
    assert "hsts-missing" in c
    assert "csp-missing" in c
    assert "xcto-missing" in c


def test_full_headers_pass():
    p = PageData(
        url="https://e.com", final_url="https://e.com", is_https=True,
        headers={
            "strict-transport-security": "max-age=63072000",
            "content-security-policy": "default-src 'self'",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
        },
    )
    assert security_checks(p) == []


def test_mixed_content_detected():
    p = PageData(url="https://e.com", final_url="https://e.com", is_https=True,
                 headers={"content-security-policy": "x", "x-content-type-options": "nosniff",
                          "x-frame-options": "DENY", "referrer-policy": "x",
                          "strict-transport-security": "x"},
                 resource_urls=["http://cdn.com/a.js", "/local.css"])
    assert "mixed-content" in codes(security_checks(p))


def test_no_headers_skips_header_checks():
    # when we couldn't read headers, don't fabricate header findings
    p = PageData(url="https://e.com", final_url="https://e.com", is_https=True, headers={})
    assert "csp-missing" not in codes(security_checks(p))


def test_junit_output_is_valid_xml():
    import xml.etree.ElementTree as ET

    from sitedoctor.checks import Finding
    from sitedoctor.report import PageReport, SiteReport
    from sitedoctor.reporters import to_junit

    r = SiteReport(start_url="https://e.com")
    r.pages = [PageReport("https://e.com",
                          {"seo": 90, "a11y": 90, "performance": 90, "security": 70},
                          [Finding("security", "warn", "csp-missing", "Missing CSP.")])]
    xml = to_junit(r)
    root = ET.fromstring(xml)               # must parse
    assert root.tag == "testsuite"
    assert root.attrib["failures"] == "1"
