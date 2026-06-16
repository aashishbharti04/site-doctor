# 🤝 Contributing to site-doctor

Thanks for helping make the web healthier! Contributions of all sizes are welcome.

## Quick start

```bash
git clone https://github.com/aashishbharti04/site-doctor
cd site-doctor
pip install -e ".[dev]"
pytest -q
```

## Ground rules

- **Keep it zero-dependency.** Runtime code uses only the Python standard library.
- **New checks are pure functions** over `PageData` returning `Finding`s — easy to test.
  Add them in `src/sitedoctor/checks.py` and cover them in `tests/test_checks.py`.
- Run `pytest -q` before opening a PR; CI runs it on Linux + Windows, Python 3.9–3.13.

## Good first contributions

- New SEO/a11y/performance checks (e.g. favicon, hreflang, duplicate titles across pages).
- New output formats (Markdown report, HTML report, JUnit XML for CI).
- A `--sitemap` mode that audits every URL in `sitemap.xml`.

## Reporting bugs

Open an issue with the command you ran, the target URL, and the output (redact anything private).

By contributing you agree your work is licensed under the project's [MIT License](LICENSE).
