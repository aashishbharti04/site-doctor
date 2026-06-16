"""Export a SiteReport to Markdown or a self-contained HTML file."""

from __future__ import annotations

import csv as _csv
import html as _html
from collections import Counter

from .report import SiteReport


def _aggregate(report: SiteReport):
    """Collapse per-page findings into (severity, category, message) -> page count."""
    counter: Counter = Counter()
    msg: dict = {}
    for p in report.pages:
        for f in p.findings:
            key = (f.severity, f.category, f.code)
            counter[key] += 1
            msg.setdefault(key, f.message)
    sev_rank = {"error": 0, "warn": 1, "info": 2}
    rows = sorted(counter.items(), key=lambda kv: (sev_rank[kv[0][0]], -kv[1]))
    return [(sev, cat, msg[(sev, cat, code)], n) for (sev, cat, code), n in rows]


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def to_markdown(report: SiteReport) -> str:
    s = report.scores
    out = [
        f"# site-doctor report — {report.start_url}",
        "",
        f"**Health Score:** {report.overall:.1f}/100 — {report.grade}  ",
        f"Pages audited: {len(report.pages)} · Links checked: {report.links_checked}",
        "",
        "## Scores",
        "",
        "| Category | Score |",
        "|----------|------:|",
        f"| SEO | {s.get('seo', 0):.1f} |",
        f"| Accessibility | {s.get('a11y', 0):.1f} |",
        f"| Performance | {s.get('performance', 0):.1f} |",
        f"| Links | {s.get('links', 0):.1f} |",
        "",
        "## Issues",
        "",
    ]
    rows = _aggregate(report)
    if rows:
        out += ["| Severity | Category | Issue | Pages |",
                "|----------|----------|-------|------:|"]
        for sev, cat, message, n in rows:
            out.append(f"| {sev} | {cat} | {message} | {n} |")
    else:
        out.append("No SEO/accessibility/performance issues found. ✅")
    out += ["", "## Broken links", ""]
    if report.broken_links:
        out += ["| Status | URL |", "|--------|-----|"]
        for r in report.broken_links:
            out.append(f"| {r.status or r.error or 'error'} | {r.url} |")
    else:
        out.append("No broken links found. ✅")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def write_csv(report: SiteReport, path: str) -> None:
    """Write all issues and links to a CSV (great for spreadsheets/clients)."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = _csv.writer(fh)
        w.writerow(["type", "page_or_url", "category", "severity", "code", "message"])
        for p in report.pages:
            for f in p.findings:
                w.writerow(["issue", p.url, f.category, f.severity, f.code, f.message])
        for f in report.site_findings:
            w.writerow(["site-issue", report.start_url, f.category, f.severity,
                        f.code, f.message])
        for r in report.broken_links:
            w.writerow(["broken-link", r.url, "links", "error", r.status, r.error])
        for r in report.unverified_links:
            w.writerow(["unverified-link", r.url, "links", "info", r.status, r.error])


# ---------------------------------------------------------------------------
# HTML (self-contained, dark-neon)
# ---------------------------------------------------------------------------
_SEV_COLOR = {"error": "#ff5470", "warn": "#ffb020", "info": "#8b97a7"}


def _score_color(v: float) -> str:
    return "#00ffa3" if v >= 75 else "#ffb020" if v >= 50 else "#ff5470"


def _bar(v: float) -> str:
    return (f'<div class="bar"><span style="width:{max(0, min(100, v))}%;'
            f'background:{_score_color(v)}"></span></div>')


def to_html(report: SiteReport) -> str:
    e = _html.escape
    s = report.scores
    rows = _aggregate(report)

    issue_rows = "".join(
        f'<tr><td><span class="sev" style="color:{_SEV_COLOR[sev]}">{sev}</span></td>'
        f"<td>{e(cat)}</td><td>{e(message)}</td><td class='num'>{n}</td></tr>"
        for sev, cat, message, n in rows
    ) or '<tr><td colspan="4">No issues found ✅</td></tr>'

    broken_rows = "".join(
        f"<tr><td class='num'>{e(str(r.status or r.error or 'error'))}</td>"
        f'<td><a href="{e(r.url)}">{e(r.url)}</a></td></tr>'
        for r in report.broken_links
    ) or '<tr><td colspan="2">No broken links ✅</td></tr>'

    def cat_row(label, val):
        return (f'<div class="catrow"><span class="catlabel">{label}</span>'
                f'{_bar(val)}<span class="catnum">{val:.1f}</span></div>')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>site-doctor report — {e(report.start_url)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ font-family: system-ui, sans-serif; background:#0d1117; color:#e6edf3;
         margin:0; padding:40px; line-height:1.5; }}
  .wrap {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 22px; }} h2 {{ margin-top: 36px; font-size: 18px; }}
  .url {{ color:#00e5ff; word-break: break-all; }}
  .score {{ font-size: 48px; font-weight: 800; color:{_score_color(report.overall)}; }}
  .grade {{ color:#ffb020; font-weight:600; }}
  .meta {{ color:#8b97a7; font-size: 14px; }}
  .catrow {{ display:flex; align-items:center; gap:12px; margin:10px 0; }}
  .catlabel {{ width:120px; font-size:14px; }}
  .catnum {{ width:48px; text-align:right; font-variant-numeric: tabular-nums; }}
  .bar {{ flex:1; height:12px; background:#1c2230; border-radius:6px; overflow:hidden; }}
  .bar span {{ display:block; height:100%; border-radius:6px; }}
  table {{ width:100%; border-collapse: collapse; margin-top:10px; font-size:14px; }}
  th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid #283041; }}
  th {{ color:#8b97a7; font-weight:600; }}
  .num {{ text-align:right; font-variant-numeric: tabular-nums; }}
  .sev {{ font-weight:700; text-transform:uppercase; font-size:12px; }}
  a {{ color:#00e5ff; }}
  footer {{ margin-top:40px; color:#8b97a7; font-size:13px; }}
</style></head>
<body><div class="wrap">
  <h1>🩺 site-doctor report</h1>
  <p class="url">{e(report.start_url)}</p>
  <p><span class="score">{report.overall:.1f}</span><span class="meta">/100</span>
     &nbsp; <span class="grade">{e(report.grade)}</span></p>
  <p class="meta">Pages audited: {len(report.pages)} · Links checked: {report.links_checked}</p>

  <h2>Scores</h2>
  {cat_row("SEO", s.get("seo", 0))}
  {cat_row("Accessibility", s.get("a11y", 0))}
  {cat_row("Performance", s.get("performance", 0))}
  {cat_row("Links", s.get("links", 0))}

  <h2>Issues</h2>
  <table><thead><tr><th>Severity</th><th>Category</th><th>Issue</th><th class="num">Pages</th></tr></thead>
  <tbody>{issue_rows}</tbody></table>

  <h2>Broken links</h2>
  <table><thead><tr><th class="num">Status</th><th>URL</th></tr></thead>
  <tbody>{broken_rows}</tbody></table>

  <footer>Generated by <a href="https://github.com/aashishbharti04/site-doctor">site-doctor</a>.</footer>
</div></body></html>
"""
