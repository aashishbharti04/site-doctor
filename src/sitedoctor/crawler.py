"""Same-domain crawler (stdlib only). Fetches HTML pages breadth-first."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections import deque
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urldefrag, urlparse

from .parser import PageData, parse_html, same_domain

USER_AGENT = "site-doctor/0.1 (+https://github.com/aashishbharti04/site-doctor)"


def fetch(url: str, timeout: int = 15):
    """Return (status, html_or_none, content_type, error_or_none)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "text/html" not in ctype:
                return resp.status, None, ctype, None
            raw = resp.read(3_000_000)  # cap at ~3 MB
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, raw.decode(charset, "replace"), ctype, None
    except urllib.error.HTTPError as e:
        return e.code, None, "", f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return 0, None, "", str(e.reason)
    except Exception as e:  # noqa: BLE001 - report anything else as an error
        return 0, None, "", str(e)


def _robots_for(start_url: str, obey: bool):
    if not obey:
        return None
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp
    except Exception:  # noqa: BLE001 - missing/broken robots = crawl freely
        return None


def crawl(start_url: str, max_pages: int = 20, max_depth: int = 2,
          obey_robots: bool = True, timeout: int = 15):
    """Crawl same-domain HTML pages. Returns (pages, skipped_robots)."""
    rp = _robots_for(start_url, obey_robots)
    seen: set[str] = set()
    pages: list[PageData] = []
    skipped_robots = 0
    queue: deque[tuple[str, int]] = deque([(urldefrag(start_url).url, 0)])

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        if rp is not None and not rp.can_fetch(USER_AGENT, url):
            skipped_robots += 1
            continue

        status, html, _ctype, err = fetch(url, timeout)
        if html is None:
            # Non-HTML or failed fetch: don't score it as a page. A bad status on
            # an internal URL still surfaces through the broken-link checker.
            continue

        page = parse_html(html, base_url=url)
        page.url = url
        pages.append(page)

        if depth < max_depth:
            for link in page.links:
                target = urldefrag(link.href).url
                if target not in seen and same_domain(target, start_url):
                    if target.startswith(("http://", "https://")):
                        queue.append((target, depth + 1))

    return pages, skipped_robots
