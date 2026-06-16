"""Same-domain crawler (stdlib only). Fetches HTML pages breadth-first."""

from __future__ import annotations

import urllib.error
import urllib.request
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
          obey_robots: bool = True, timeout: int = 15, workers: int = 8):
    """Crawl same-domain HTML pages concurrently, level by level (BFS).

    Returns (pages, skipped_robots).
    """
    from concurrent.futures import ThreadPoolExecutor

    rp = _robots_for(start_url, obey_robots)
    seen: set[str] = {urldefrag(start_url).url}
    pages: list[PageData] = []
    skipped_robots = 0
    frontier = [urldefrag(start_url).url]
    depth = 0

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        while frontier and depth <= max_depth and len(pages) < max_pages:
            # respect robots.txt for this level
            allowed = []
            for url in frontier:
                if rp is not None and not rp.can_fetch(USER_AGENT, url):
                    skipped_robots += 1
                else:
                    allowed.append(url)

            remaining = max_pages - len(pages)
            allowed = allowed[:remaining]

            fetched = list(pool.map(lambda u: (u, fetch(u, timeout)), allowed))

            next_frontier: list[str] = []
            for url, (_status, html, _ctype, _err) in fetched:
                if html is None:
                    continue
                page = parse_html(html, base_url=url)
                page.url = url
                pages.append(page)
                if depth < max_depth:
                    for link in page.links:
                        target = urldefrag(link.href).url
                        if (target not in seen and same_domain(target, start_url)
                                and target.startswith(("http://", "https://"))):
                            seen.add(target)
                            next_frontier.append(target)

            frontier = next_frontier
            depth += 1

    return pages, skipped_robots
