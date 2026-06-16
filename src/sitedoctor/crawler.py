"""Same-domain crawler (stdlib only). Fetches HTML pages breadth-first."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urldefrag, urlparse

from .parser import PageData, parse_html, same_domain

USER_AGENT = "site-doctor/0.3 (+https://github.com/aashishbharti04/site-doctor)"


@dataclass
class FetchResult:
    status: int = 0
    html: str | None = None
    content_type: str = ""
    error: str | None = None
    headers: dict = field(default_factory=dict)   # lowercased header names
    elapsed_ms: float = 0.0
    final_url: str = ""


def _lower_headers(resp) -> dict:
    try:
        return {k.lower(): v for k, v in resp.headers.items()}
    except Exception:  # noqa: BLE001
        return {}


def _ssl_context(insecure: bool):
    if not insecure:
        return None
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch(url: str, timeout: int = 15, user_agent: str | None = None,
          insecure: bool = False) -> FetchResult:
    """Fetch a URL, returning a FetchResult with timing, headers and final URL."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent or USER_AGENT})
    ctx = _ssl_context(insecure)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            ctype = resp.headers.get("Content-Type", "")
            headers = _lower_headers(resp)
            final_url = resp.url
            if "text/html" not in ctype:
                elapsed = (time.perf_counter() - start) * 1000
                return FetchResult(resp.status, None, ctype,
                                   f"non-HTML content ({ctype or 'unknown'})",
                                   headers, elapsed, final_url)
            raw = resp.read(3_000_000)  # cap at ~3 MB
            charset = resp.headers.get_content_charset() or "utf-8"
            elapsed = (time.perf_counter() - start) * 1000
            return FetchResult(resp.status, raw.decode(charset, "replace"), ctype,
                               None, headers, elapsed, final_url)
    except urllib.error.HTTPError as e:
        return FetchResult(e.code, None, "", f"HTTP {e.code}", final_url=url)
    except urllib.error.URLError as e:
        return FetchResult(0, None, "", str(e.reason), final_url=url)
    except Exception as e:  # noqa: BLE001 - report anything else as an error
        return FetchResult(0, None, "", str(e), final_url=url)


def _attach_meta(page: PageData, fr: "FetchResult", url: str) -> None:
    """Copy network metadata from a FetchResult onto a parsed PageData."""
    page.status = fr.status
    page.headers = fr.headers
    page.load_ms = fr.elapsed_ms
    page.final_url = fr.final_url or url
    page.is_https = (fr.final_url or url).startswith("https://")


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
          obey_robots: bool = True, timeout: int = 15, workers: int = 8,
          user_agent: str | None = None, insecure: bool = False):
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

            fetched = list(pool.map(
                lambda u: (u, fetch(u, timeout, user_agent, insecure)), allowed))

            next_frontier: list[str] = []
            for url, fr in fetched:
                if fr.html is None:
                    continue
                page = parse_html(fr.html, base_url=url)
                page.url = url
                _attach_meta(page, fr, url)
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
