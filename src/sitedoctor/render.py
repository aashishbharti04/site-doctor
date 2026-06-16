"""Render a SiteReport to a colored terminal string (ASCII/no-color fallbacks)."""

from __future__ import annotations

import os
import sys
from collections import Counter

from .report import SiteReport

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_GREY = "\033[90m"


def _color_on(flag):
    if flag is not None:
        return flag
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _unicode_on():
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "█░✓✗".encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _c(text, color, on):
    return f"{color}{text}{_RESET}" if on else text


def _bar(frac, width, on, full, empty):
    frac = max(0.0, min(1.0, frac))
    n = round(frac * width)
    color = _GREEN if frac >= 0.75 else _YELLOW if frac >= 0.5 else _RED
    return _c(full * n + empty * (width - n), color, on)


def render(report: SiteReport, color=None) -> str:
    on = _color_on(color)
    uni = _unicode_on()
    full, empty = ("█", "░") if uni else ("#", "-")
    check, cross = ("✓", "✗") if uni else ("OK", "X")
    out: list[str] = []

    out.append(_c(f"\n  site-doctor — {report.start_url}", _BOLD + _CYAN, on))
    out.append(_c(f"  Pages audited: {len(report.pages)}"
                  + (f"  ·  Links checked: {report.links_checked}"
                     if report.links_checked else ""), _GREY, on))
    out.append("")

    out.append(_c(f"  Health Score: {report.overall:.1f}/100", _BOLD + _GREEN, on))
    out.append(_c(f"  Grade: {report.grade}", _BOLD + _YELLOW, on))
    out.append("")

    labels = {"seo": "SEO", "a11y": "Accessibility", "performance": "Performance",
              "links": "Links"}
    width = max(len(v) for v in labels.values())
    for key in ("seo", "a11y", "performance", "links"):
        sc = report.scores.get(key, 0)
        line = (f"  {labels[key].ljust(width)}  {_bar(sc/100, 18, on, full, empty)} "
                f"{sc:5.1f}/100")
        out.append(line)
    out.append("")

    # aggregate findings across pages by severity + code
    counter: Counter = Counter()
    examples: dict = {}
    for p in report.pages:
        for f in p.findings:
            counter[(f.category, f.severity, f.code)] += 1
            examples.setdefault((f.category, f.severity, f.code), f.message)
    for f in report.site_findings:  # cross-page (site-wide) issues
        counter[(f.category, f.severity, f.code)] += 1
        examples[(f.category, f.severity, f.code)] = f.message

    if counter:
        out.append(_c("  Top issues", _BOLD + _MAGENTA, on))
        sev_rank = {"error": 0, "warn": 1, "info": 2}
        sev_color = {"error": _RED, "warn": _YELLOW, "info": _GREY}
        for (cat, sev, code), n in sorted(
                counter.items(), key=lambda kv: (sev_rank[kv[0][1]], -kv[1]))[:12]:
            tag = _c(f"[{sev}]", sev_color[sev], on)
            pages_txt = f"{n} page{'s' if n > 1 else ''}"
            out.append(f"  {tag} {_c(cat, _CYAN, on)}: {examples[(cat, sev, code)]} "
                       + _c(f"({pages_txt})", _GREY, on))
    else:
        out.append(_c("  No SEO/a11y/performance issues found. " + check, _GREEN, on))
    out.append("")

    if report.broken_links:
        out.append(_c(f"  Broken links ({len(report.broken_links)})", _BOLD + _RED, on))
        for r in report.broken_links[:15]:
            status = r.status or r.error or "error"
            out.append(f"  {_c(cross, _RED, on)} {status}  {r.url}")
        if len(report.broken_links) > 15:
            out.append(_c(f"  …and {len(report.broken_links) - 15} more", _GREY, on))
    else:
        out.append(_c(f"  No broken links. {check}", _GREEN, on))

    if report.unverified_links:
        out.append("")
        out.append(_c(f"  Could not verify ({len(report.unverified_links)}) "
                      "— bot-blocked or unreachable, not counted against score",
                      _BOLD + _YELLOW, on))
        for r in report.unverified_links[:8]:
            status = r.status or r.error or "error"
            out.append(_c(f"  ? {status}  {r.url}", _GREY, on))
        if len(report.unverified_links) > 8:
            out.append(_c(f"  …and {len(report.unverified_links) - 8} more", _GREY, on))

    if report.links_truncated:
        out.append(_c(f"  (note: {report.links_truncated} extra links not checked "
                      "— raise --max-links)", _GREY, on))
    if report.skipped_robots:
        out.append(_c(f"  (note: {report.skipped_robots} URLs skipped per robots.txt)",
                      _GREY, on))
    out.append("")
    return "\n".join(out)
