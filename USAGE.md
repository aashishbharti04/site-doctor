# 📖 site-doctor — User Manual

A beginner-friendly guide: what site-doctor is, how to install it, and how to use it.

---

## What is site-doctor?

`site-doctor` is a command-line tool that **crawls a website and checks its health** across
four areas, then gives you a score out of 100:

- 🔍 **SEO** — title, meta description, headings, Open Graph, canonical, structured data,
  and **duplicate titles/descriptions across pages**
- ♿ **Accessibility** — image alt text, page language, link text, form labels
- ⚡ **Performance** — measured **page load time**, page size, scripts/stylesheets, images
- 🔒 **Security** — HTTPS, security headers (HSTS, CSP, etc.), mixed content
- 🔗 **Broken links** — checks every link's status (bot-blocked links are flagged
  separately, not counted against your score)

It's perfect for quickly auditing a client site or your own project before launch.

---

## Install

You need **Python 3.9+**. Then, in a terminal:

```bash
pip install site-doctor
```

### ⚠️ "site-doctor is not recognized" — how to fix

If you run `site-doctor` and Windows says *"The term 'site-doctor' is not recognized…"*,
the install worked but Python's scripts folder isn't on your PATH. Two fixes:

**Option A — run it this way instead (always works):**
```bash
python -m sitedoctor https://example.com
```

**Option B — add scripts to PATH once, then reopen PowerShell:**
```powershell
setx PATH "$($env:PATH);C:\Users\DELL\AppData\Roaming\Python\Python314\Scripts"
```
(Replace the path if your Python version/username differs. Find it with:
`python -c "import sysconfig;print(sysconfig.get_path('scripts'))"`)

---

## Your first audit

```bash
python -m sitedoctor https://example.com
```

You'll see the **PGLU** banner, then a report like:

```
  Health Score: 82.4/100
  Grade: B — good

  SEO            ████████████████░░  88.0/100
  Accessibility  ██████████████░░░░  79.0/100
  Performance    ██████████████████  96.0/100
  Links          ████████████████░░  88.0/100

  Top issues
  [error] a11y: 4/9 images missing an alt attribute. (7 pages)
  ...
  Broken links (2)
  ✗ 404  https://example.com/old-page
```

### How to read it
- **Health Score / Grade** — overall health (A is best, F is worst).
- **Bars** — score per category; green = good, yellow = okay, red = needs work.
- **Top issues** — the most important problems, worst first, with how many pages each affects.
- **Broken links** — links that returned an error, with their status code.

---

## Common commands

```bash
# audit one page only (fast)
python -m sitedoctor example.com --max-pages 1

# crawl a bigger site
python -m sitedoctor example.com --max-pages 50 --max-depth 3

# audit every page listed in the sitemap
python -m sitedoctor example.com --sitemap

# make a client-ready HTML report file
python -m sitedoctor example.com --html report.html
#   then open it:  start report.html   (Windows)

# also save a Markdown report
python -m sitedoctor example.com --md report.md

# export a CSV of all issues & links (open in Excel/Sheets)
python -m sitedoctor example.com --csv issues.csv

# machine-readable JSON (for scripts/dashboards)
python -m sitedoctor example.com --json > report.json

# skip external links (faster), and hide the banner
python -m sitedoctor example.com --no-external --no-banner
```

---

## All options

| Flag | What it does | Default |
|------|--------------|---------|
| `--max-pages N` | Maximum pages to crawl | 20 |
| `--max-depth N` | How deep to follow links | 2 |
| `--max-links N` | Maximum links to check | 200 |
| `--timeout N` | Per-request timeout (seconds) | 15 |
| `--sitemap` | Audit URLs from `sitemap.xml` instead of crawling | off |
| `--sitemap-url URL` | Use a specific sitemap URL (implies `--sitemap`) | — |
| `--html PATH` | Also write a self-contained HTML report | — |
| `--md PATH` | Also write a Markdown report | — |
| `--csv PATH` | Also write a CSV of all issues & links | — |
| `--junit PATH` | Also write a JUnit XML report (for CI) | — |
| `--ignore CODE` | Suppress a check by code (repeatable) | — |
| `--min-seo / --min-a11y / --min-performance / --min-security / --min-links N` | Fail if that category's score is below N | — |
| `--json` | Print JSON instead of the report | off |
| `--fail-under N` | Exit with an error if the score is below N (for CI) | — |
| `--no-external` | Don't check external links | off |
| `--browser-ua` | Send a desktop-browser User-Agent (for sites that block bots) | off |
| `--user-agent UA` | Custom User-Agent string | — |
| `--insecure` | Skip TLS certificate verification | off |
| `--no-robots` | Ignore `robots.txt` | off |
| `--no-color` | Plain text, no colors | off |
| `--no-banner` | Hide the PGLU banner | off |
| `--version` | Show the version | — |
| `--help` | Show all options | — |

---

## Use it in CI/CD (gate deploys on site health)

```yaml
# .github/workflows/site-health.yml
- run: |
    pip install site-doctor
    site-doctor https://your-site.com --fail-under 80
```

The build fails if the health score drops below 80 — catch SEO/accessibility
regressions before they ship.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `site-doctor not recognized` | Use `python -m sitedoctor …` or add scripts to PATH (above) |
| `could not fetch any HTML pages` | The tool now prints the real reason + a hint. Common fixes: `--browser-ua` (site blocks bots), `--insecure` (TLS cert error), bigger `--timeout` (slow site). |
| Works in my browser but not here | A WAF/firewall is likely blocking automated requests — try `--browser-ua`. |
| `certificate verify failed` | Add `--insecure`, or update your system/Python CA certificates. |
| Audit is slow | Lower `--max-pages`, add `--no-external`, or lower `--max-links` |
| Garbled characters on old terminals | They auto-fall back to plain ASCII; or add `--no-color` |

---

## Questions or ideas?

Open an issue or PR on the [repo](https://github.com/aashishbharti04/site-doctor).
See [CONTRIBUTING.md](CONTRIBUTING.md) to add new checks.
