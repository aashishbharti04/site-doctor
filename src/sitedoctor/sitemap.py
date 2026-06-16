"""Fetch and parse sitemap.xml (including sitemap-index files)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

from .crawler import fetch


def _locs(xml_text: str) -> tuple[list[str], list[str]]:
    """Return (page_urls, child_sitemap_urls) from a sitemap XML document."""
    page_urls: list[str] = []
    child_sitemaps: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return page_urls, child_sitemaps

    # Tags are namespaced; match on the local name. Distinguish
    # <sitemap><loc> (a sitemap index) from <url><loc> (a urlset).
    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in ("url", "sitemap"):
            loc = None
            for child in elem:
                if child.tag.rsplit("}", 1)[-1] == "loc" and child.text:
                    loc = child.text.strip()
                    break
            if not loc:
                continue
            if tag == "sitemap":
                child_sitemaps.append(loc)
            else:
                page_urls.append(loc)
    return page_urls, child_sitemaps


def fetch_sitemap_urls(start_url: str, sitemap_url: str | None = None,
                       timeout: int = 15, limit: int = 1000,
                       max_sitemaps: int = 25) -> list[str]:
    """Return page URLs from a site's sitemap, following sitemap-index files."""
    if sitemap_url is None:
        parsed = urlparse(start_url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    to_visit = [sitemap_url]
    seen_sitemaps: set[str] = set()
    pages: list[str] = []

    while to_visit and len(seen_sitemaps) < max_sitemaps and len(pages) < limit:
        sm = to_visit.pop(0)
        if sm in seen_sitemaps:
            continue
        seen_sitemaps.add(sm)

        _status, body, _ctype, _err = _fetch_text(sm, timeout)
        if not body:
            continue
        page_urls, child_sitemaps = _locs(body)
        pages.extend(page_urls)
        for child in child_sitemaps:
            to_visit.append(urljoin(sm, child))

    # de-dupe, preserve order, cap
    return list(dict.fromkeys(pages))[:limit]


def _fetch_text(url: str, timeout: int):
    """Like crawler.fetch but accepts XML content types too."""
    import urllib.error
    import urllib.request

    from .crawler import USER_AGENT

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(5_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, raw.decode(charset, "replace"), \
                resp.headers.get("Content-Type", ""), None
    except urllib.error.HTTPError as e:
        return e.code, None, "", f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return 0, None, "", str(e.reason)
    except Exception as e:  # noqa: BLE001
        return 0, None, "", str(e)
