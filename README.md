<div align="center">

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

## ✨ What it checks

| Category | Examples |
|----------|----------|
| 🔍 **SEO** | title length, meta description, single H1, canonical, Open Graph, viewport, JSON-LD, thin content |
| ♿ **Accessibility** | `<html lang>`, image alt text, vague/empty link text, form-field labels, heading hierarchy |
| ⚡ **Performance** | HTML size, script/stylesheet count, large inline JS, image count (heuristics from HTML) |
| 🔗 **Broken links** | parallel HTTP checks of internal **and** external links, with status codes |

Plus a weighted **overall health score** and letter grade.

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
```

### Options

| Flag | Description |
|------|-------------|
| `--max-pages N` | Max pages to crawl (default 20) |
| `--max-depth N` | Max crawl depth (default 2) |
| `--max-links N` | Max links to check (default 200) |
| `--timeout N` | Per-request timeout in seconds (default 15) |
| `--no-robots` | Ignore `robots.txt` (it's respected by default) |
| `--no-external` | Don't check external links |
| `--fail-under N` | Exit non-zero if health score < N |
| `--json` / `--no-color` | JSON output / plain text |

## 🤖 Gate your deploys on site health (GitHub Actions)

```yaml
- name: Audit site health
  run: |
    pip install site-doctor
    site-doctor https://your-site.com --fail-under 80
```

The build fails if SEO/a11y/performance/links regress below your threshold.

## 🧱 How it works

Pure standard library: a breadth-first crawler (`urllib`), an `html.parser`-based
extractor, pure-function check rules, weighted scoring, and a `ThreadPoolExecutor`-powered
parallel link checker. No browser, no third-party packages.

```
crawler → parser → checks (seo/a11y/perf) → scoring → report → render
                                  links checker ↗
```

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
