"""Parallel link checker with industry-aware classification (stdlib only).

Distinguishes genuinely *broken* links (4xx/5xx) from links we simply *couldn't
verify* — bot-blocked (403/405/429/999) or unreachable (DNS/timeout/refused).
Only genuinely broken links count against the health score.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .crawler import USER_AGENT

# Statuses that usually mean "the server is up but blocking automated checks",
# not that the link is dead. Common for LinkedIn (999), social networks, WAFs.
_BLOCKED_STATUSES = {401, 403, 405, 429, 999}


@dataclass
class LinkResult:
    url: str
    status: int          # HTTP status, or 0 for a connection error
    kind: str            # "ok" | "broken" | "blocked" | "unreachable"
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.kind == "ok"


def classify(status: int) -> str:
    if 200 <= status < 400:
        return "ok"
    if status == 0:
        return "unreachable"
    if status in _BLOCKED_STATUSES:
        return "blocked"
    return "broken"  # 404, 410, other 4xx, all 5xx


def _check_one(url: str, timeout: int) -> LinkResult:
    # Try HEAD first (cheap); fall back to GET if the server rejects HEAD.
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method,
                                     headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return LinkResult(url, resp.status, classify(resp.status))
        except urllib.error.HTTPError as e:
            if e.code in (403, 405) and method == "HEAD":
                continue  # some servers only allow GET
            return LinkResult(url, e.code, classify(e.code), f"HTTP {e.code}")
        except urllib.error.URLError as e:
            return LinkResult(url, 0, "unreachable", str(e.reason))
        except Exception as e:  # noqa: BLE001
            return LinkResult(url, 0, "unreachable", str(e))
    return LinkResult(url, 0, "unreachable", "unreachable")


def check_links(urls, timeout: int = 10, workers: int = 16, max_links: int = 200):
    """Check up to ``max_links`` unique URLs concurrently.

    Returns (results, truncated_count).
    """
    unique = list(dict.fromkeys(urls))  # de-dupe, keep order
    truncated = max(0, len(unique) - max_links)
    unique = unique[:max_links]

    results: list[LinkResult] = []
    if not unique:
        return results, truncated

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_check_one, u, timeout): u for u in unique}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results, truncated
