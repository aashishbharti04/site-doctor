"""Orchestrate a full site audit and assemble a SiteReport."""

from __future__ import annotations

from dataclasses import dataclass, field

from .checks import Finding, run_all
from .crawler import crawl
from .links import LinkResult, check_links
from .scoring import SEVERITY_PENALTY, grade, links_score, overall_score, score_page


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
    unverified_links: list[LinkResult] = field(default_factory=list)
    site_findings: list[Finding] = field(default_factory=list)   # cross-page issues
    links_checked: int = 0
    links_truncated: int = 0
    skipped_robots: int = 0


def _cross_page_findings(pages) -> list[Finding]:
    """Site-wide SEO checks that need all pages at once (duplicate title/meta)."""
    findings: list[Finding] = []
    from collections import defaultdict

    titles = defaultdict(list)
    descs = defaultdict(list)
    for p in pages:
        title = (p.title or "").strip()
        desc = (p.meta.get("description", "") or "").strip()
        if title:
            titles[title].append(p.url)
        if desc:
            descs[desc].append(p.url)

    for title, urls in titles.items():
        if len(urls) > 1:
            findings.append(Finding("seo", "warn", "duplicate-title",
                                    f'Duplicate <title> on {len(urls)} pages: "{title[:50]}"'))
    for _desc, urls in descs.items():
        if len(urls) > 1:
            findings.append(Finding("seo", "warn", "duplicate-meta-desc",
                                    f"Duplicate meta description on {len(urls)} pages."))
    return findings


def _avg(values: list[int]) -> float:
    return round(sum(values) / len(values), 1) if values else 100.0


def _pages_from_sitemap(start_url, sitemap_url, max_pages, timeout):
    """Fetch and parse the pages listed in a site's sitemap (no link-following)."""
    from .crawler import fetch
    from .parser import parse_html
    from .sitemap import fetch_sitemap_urls

    from .crawler import _attach_meta

    urls = fetch_sitemap_urls(start_url, sitemap_url, timeout=timeout, limit=max_pages)
    pages = []
    for url in urls[:max_pages]:
        fr = fetch(url, timeout)
        if fr.html is None:
            continue
        page = parse_html(fr.html, base_url=url)
        page.url = url
        _attach_meta(page, fr, url)
        pages.append(page)
    return pages, 0


def audit(start_url: str, *, max_pages: int = 20, max_depth: int = 2,
          obey_robots: bool = True, timeout: int = 15, max_links: int = 200,
          check_external: bool = True, use_sitemap: bool = False,
          sitemap_url: str | None = None, ignore: set[str] | None = None) -> SiteReport:
    ignore = ignore or set()
    if use_sitemap:
        pages, skipped = _pages_from_sitemap(start_url, sitemap_url, max_pages, timeout)
    else:
        pages, skipped = crawl(start_url, max_pages=max_pages, max_depth=max_depth,
                               obey_robots=obey_robots, timeout=timeout)

    report = SiteReport(start_url=start_url, skipped_robots=skipped)
    if not pages:
        report.scores = {"seo": 0, "a11y": 0, "performance": 0, "security": 0, "links": 0}
        report.grade = grade(0)
        return report

    for page in pages:
        findings = [f for f in run_all(page) if f.code not in ignore]
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
    broken = [r for r in results if r.kind == "broken"]
    unverified = [r for r in results if r.kind in ("blocked", "unreachable")]

    # cross-page (site-wide) SEO findings, e.g. duplicate titles/descriptions
    site_findings = [f for f in _cross_page_findings(pages) if f.code not in ignore]
    site_seo_penalty = sum(SEVERITY_PENALTY[f.severity] for f in site_findings)

    seo = max(0.0, _avg([p.scores["seo"] for p in report.pages]) - site_seo_penalty)
    a11y = _avg([p.scores["a11y"] for p in report.pages])
    perf = _avg([p.scores["performance"] for p in report.pages])
    security = _avg([p.scores["security"] for p in report.pages])
    # only genuinely broken links count against the score (not bot-blocked ones)
    links = links_score(len(results), len(broken))

    report.scores = {"seo": round(seo, 1), "a11y": a11y, "performance": perf,
                     "security": security, "links": links}
    report.overall = overall_score(seo, a11y, perf, security, links)
    report.grade = grade(report.overall)
    report.broken_links = broken
    report.unverified_links = unverified
    report.site_findings = site_findings
    report.links_checked = len(results)
    report.links_truncated = truncated
    return report


def _is_external(url: str, root: str) -> bool:
    from urllib.parse import urlparse
    return urlparse(url).netloc != urlparse(root).netloc
