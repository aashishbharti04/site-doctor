<div align="center">

```text
██████╗  ██████╗ ██╗     ██╗   ██╗
██╔══██╗██╔════╝ ██║     ██║   ██║
██████╔╝██║  ███╗██║     ██║   ██║
██╔═══╝ ██║   ██║██║     ██║   ██║
██║     ╚██████╔╝███████╗╚██████╔╝
╚═╝      ╚═════╝ ╚══════╝ ╚═════╝
PGLU · site-doctor
```

# 🩺 site-doctor

### Crawl any website and audit **SEO · Accessibility · Performance · Broken links** — from your terminal.

An agency-grade website health checker in pure Python. Get a scored report in seconds,
output JSON for dashboards, or gate your CI/CD on a minimum health score.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-00E5FF?style=for-the-badge&logo=python&logoColor=white&labelColor=0D1117">
  <img alt="Zero deps" src="https://img.shields.io/badge/Dependencies-ZERO-FF2E97?style=for-the-badge&labelColor=0D1117">
  <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/aashishbharti04/site-doctor/ci.yml?style=for-the-badge&logo=githubactions&logoColor=white&labelColor=0D1117&color=00FFA3">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-9D4EFF?style=for-the-badge&labelColor=0D1117">
</p>

</div>

---

```text
  site-doctor — https://example.com
  Pages audited: 12  ·  Links checked: 140

  Health Score: 82.4/100
  Grade: B — good

  SEO            ████████████████░░  88.0/100
  Accessibility  ██████████████░░░░  79.0/100
  Performance    ██████████████████  96.0/100
  Links          ████████████████░░  88.0/100

  Top issues
  [error] a11y: 4/9 images missing an alt attribute. (7 pages)
  [warn]  seo:  Meta description is 182 chars (>160). (3 pages)
  ...
  Broken links (2)
  ✗ 404  https://example.com/old-page
```

> 📖 New here? Read the **[full User Manual (USAGE.md)](USAGE.md)** — install, first
> audit, every option, and troubleshooting (including the "command not recognized" fix).

## ✨ What it checks

| Category | Examples |
|----------|----------|
| 🔍 **SEO** | title length, meta description, single H1, canonical, Open Graph, viewport, JSON-LD, thin content |
| ♿ **Accessibility** | `<html lang>`, image alt text, vague/empty link text, form-field labels, heading hierarchy |
| ⚡ **Performance** | measured page **load time**, HTML size, script/stylesheet count, large inline JS, image count |
| 🔒 **Security** | HTTPS, security headers (HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy), mixed content |
| 🔗 **Broken links** | parallel HTTP checks of internal **and** external links, with status codes |
| 🗂️ **Site-wide** | duplicate `<title>` and duplicate meta descriptions across pages |

Plus a weighted **overall health score** and letter grade.

**Smart link checking:** genuinely broken links (4xx/5xx) hurt your score, but links that
merely **can't be verified** — bot-blocked (LinkedIn `999`, social WAFs) or unreachable —
are reported separately and **don't** unfairly tank your score. Crawling is **concurrent**,
and ANSI colors work even in legacy Windows consoles.

## 🚀 Install

```bash
pip install site-doctor
```

Or run from source (no install): `PYTHONPATH=src python -m sitedoctor <url>`

## 🕹️ Usage

```bash
site-doctor example.com                  # full audit (crawls up to 20 pages)
site-doctor https://mysite.com --max-pages 50 --max-depth 3
site-doctor mysite.com --json > report.json    # machine-readable
site-doctor mysite.com --no-external           # skip external link checks (faster)
site-doctor mysite.com --fail-under 80         # exit 1 if score < 80  (great for CI)

site-doctor mysite.com --sitemap               # audit every URL in /sitemap.xml
site-doctor mysite.com --html report.html      # client-ready HTML report
site-doctor mysite.com --md report.md          # Markdown report
site-doctor mysite.com --csv issues.csv        # CSV of all issues & links (spreadsheets)
```

### Options

| Flag | Description |
|------|-------------|
| `--max-pages N` | Max pages to crawl (default 20) |
| `--max-depth N` | Max crawl depth (default 2) |
| `--max-links N` | Max links to check (default 200) |
| `--timeout N` | Per-request timeout in seconds (default 15) |
| `--sitemap` | Audit URLs from `sitemap.xml` instead of crawling |
| `--sitemap-url URL` | Use an explicit sitemap URL (implies `--sitemap`) |
| `--html PATH` | Also write a self-contained HTML report |
| `--md PATH` | Also write a Markdown report |
| `--csv PATH` | Also write a CSV of all issues & links |
| `--junit PATH` | Also write a JUnit XML report (for CI test dashboards) |
| `--ignore CODE` | Suppress a check by code (repeatable), e.g. `--ignore og-missing` |
| `--min-seo / --min-a11y / --min-performance / --min-security / --min-links N` | Per-category CI gates |
| `--no-robots` | Ignore `robots.txt` (it's respected by default) |
| `--no-external` | Don't check external links |
| `--fail-under N` | Exit non-zero if health score < N |
| `--json` / `--no-color` | JSON output / plain text |
| `--no-banner` | Hide the PGLU banner |

## 🤖 Gate your deploys on site health (GitHub Actions)

```yaml
- name: Audit site health
  run: |
    pip install site-doctor
    site-doctor https://your-site.com --fail-under 80 --min-security 70 --junit site.xml
```

The build fails if the overall score — or any category you gate on — regresses below
your threshold. Emit `--junit` XML for your CI's test dashboard.

## 🧱 How it works

Pure standard library: a breadth-first crawler (`urllib`), an `html.parser`-based
extractor, pure-function check rules, weighted scoring, and a `ThreadPoolExecutor`-powered
parallel link checker. No browser, no third-party packages.

```
crawler → parser → checks (seo/a11y/perf) → scoring → report → render
                                  links checker ↗
```

## 📦 Publishing (maintainers)

Publishing to PyPI is a **manual** action via
[`publish.yml`](.github/workflows/publish.yml) using **Trusted Publishing** (no API
tokens). One-time setup on [pypi.org](https://pypi.org): *Your account → Publishing →
Add a pending publisher* with project `site-doctor`, owner `aashishbharti04`, repo
`site-doctor`, workflow `publish.yml`, environment `pypi`. Then run the workflow from the
Actions tab.

## 🛠️ Develop

```bash
pip install -e ".[dev]"
pytest -q
```

## 🤝 Contributing

New checks, output formats, or fixes are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[MIT](LICENSE) © Aashish Bharti

<div align="center">
<sub>⭐ Star it if site-doctor saved you a manual audit.</sub>
</div>
