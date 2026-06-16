"""Orchestrate a full site audit and assemble a SiteReport."""

from __future__ import annotations

from dataclasses import dataclass, field

from .checks import Finding, run_all
from .crawler import crawl
from .links import LinkResult, check_links
from .scoring import grade, links_score, overall_score, score_page


@dataclass
class PageReport:
    url: str
    scores: dict[str, int]
    findings: list[Finding]


@dataclass
class SiteReport:
    start_url: str
    pages: list[PageReport] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)   # seo,a11y,performance,links
    overall: float = 0.0
    grade: str = ""
    broken_links: list[LinkResult] = field(default_factory=list)
    links_checked: int = 0
    links_truncated: int = 0
    skipped_robots: int = 0


def _avg(values: list[int]) -> float:
    return round(sum(values) / len(values), 1) if values else 100.0


def audit(start_url: str, *, max_pages: int = 20, max_depth: int = 2,
          obey_robots: bool = True, timeout: int = 15, max_links: int = 200,
          check_external: bool = True) -> SiteReport:
    pages, skipped = crawl(start_url, max_pages=max_pages, max_depth=max_depth,
                           obey_robots=obey_robots, timeout=timeout)

    report = SiteReport(start_url=start_url, skipped_robots=skipped)
    if not pages:
        report.scores = {"seo": 0, "a11y": 0, "performance": 0, "links": 0}
        report.grade = grade(0)
        return report

    for page in pages:
        findings = run_all(page)
        report.pages.append(PageReport(page.url, score_page(findings), findings))

    # gather links to check
    all_links: list[str] = []
    for page in pages:
        for link in page.links:
            if not link.href.startswith(("http://", "https://")):
                continue
            if not check_external and _is_external(link.href, start_url):
                continue
            all_links.append(link.href)

    results, truncated = check_links(all_links, timeout=min(timeout, 10),
                                     max_links=max_links)
    broken = [r for r in results if not r.ok]

    seo = _avg([p.scores["seo"] for p in report.pages])
    a11y = _avg([p.scores["a11y"] for p in report.pages])
    perf = _avg([p.scores["performance"] for p in report.pages])
    links = links_score(len(results), len(broken))

    report.scores = {"seo": seo, "a11y": a11y, "performance": perf, "links": links}
    report.overall = overall_score(seo, a11y, perf, links)
    report.grade = grade(report.overall)
    report.broken_links = broken
    report.links_checked = len(results)
    report.links_truncated = truncated
    return report


def _is_external(url: str, root: str) -> bool:
    from urllib.parse import urlparse
    return urlparse(url).netloc != urlparse(root).netloc
