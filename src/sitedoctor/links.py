"""Parallel broken-link checker (stdlib only)."""

from __future__ import annotations

import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .crawler import USER_AGENT


@dataclass
class LinkResult:
    url: str
    status: int          # HTTP status, or 0 for a connection error
    ok: bool
    error: str = ""


def _check_one(url: str, timeout: int) -> LinkResult:
    # Try HEAD first (cheap); fall back to GET if the server rejects HEAD.
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method,
                                     headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return LinkResult(url, resp.status, 200 <= resp.status < 400)
        except urllib.error.HTTPError as e:
            if e.code in (405, 403) and method == "HEAD":
                continue  # retry with GET
            return LinkResult(url, e.code, False, f"HTTP {e.code}")
        except urllib.error.URLError as e:
            return LinkResult(url, 0, False, str(e.reason))
        except Exception as e:  # noqa: BLE001
            return LinkResult(url, 0, False, str(e))
    return LinkResult(url, 0, False, "unreachable")


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
