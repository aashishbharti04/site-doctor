"""Command-line entry point for site-doctor."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from . import __version__
from .render import render
from .report import audit


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="site-doctor",
        description="Crawl a website and audit SEO, accessibility, performance & links.",
    )
    p.add_argument("url", help="start URL, e.g. https://example.com")
    p.add_argument("--max-pages", type=int, default=20, help="max pages to crawl (default 20)")
    p.add_argument("--max-depth", type=int, default=2, help="max crawl depth (default 2)")
    p.add_argument("--max-links", type=int, default=200, help="max links to check (default 200)")
    p.add_argument("--timeout", type=int, default=15, help="per-request timeout secs (default 15)")
    p.add_argument("--sitemap", action="store_true",
                   help="audit URLs from the site's sitemap.xml instead of crawling")
    p.add_argument("--sitemap-url", metavar="URL",
                   help="explicit sitemap URL (implies --sitemap)")
    p.add_argument("--no-robots", action="store_true", help="ignore robots.txt")
    p.add_argument("--no-external", action="store_true", help="skip checking external links")
    p.add_argument("--json", action="store_true", help="output JSON instead of a report")
    p.add_argument("--html", metavar="PATH", help="also write a self-contained HTML report")
    p.add_argument("--md", metavar="PATH", help="also write a Markdown report")
    p.add_argument("--fail-under", type=float, metavar="N", default=None,
                   help="exit non-zero if the health score is below N (for CI)")
    color = p.add_mutually_exclusive_group()
    color.add_argument("--color", dest="color", action="store_true", help="force color")
    color.add_argument("--no-color", dest="color", action="store_false", help="disable color")
    p.set_defaults(color=None)
    p.add_argument("--no-banner", action="store_true", help="hide the PGLU banner")
    p.add_argument("--version", action="version", version=f"site-doctor {__version__}")
    return p


def _normalize(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass

    args = build_parser().parse_args(argv)

    if not args.no_banner:
        from .banner import print_banner
        print_banner(color=args.color)

    url = _normalize(args.url)

    report = audit(
        url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        obey_robots=not args.no_robots,
        timeout=args.timeout,
        max_links=args.max_links,
        check_external=not args.no_external,
        use_sitemap=args.sitemap or bool(args.sitemap_url),
        sitemap_url=args.sitemap_url,
    )

    if not report.pages:
        print(f"error: could not fetch any HTML pages from {url}", file=sys.stderr)
        return 2

    if args.html:
        from .reporters import to_html
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(to_html(report))
        print(f"Wrote HTML report to {args.html}", file=sys.stderr)
    if args.md:
        from .reporters import to_markdown
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(report))
        print(f"Wrote Markdown report to {args.md}", file=sys.stderr)

    if args.json:
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        print(render(report, color=args.color))

    if args.fail_under is not None and report.overall < args.fail_under:
        print(f"FAIL: health score {report.overall} is below --fail-under {args.fail_under}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
