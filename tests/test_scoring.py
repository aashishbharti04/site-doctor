"""Tests for the pure scoring logic."""

from __future__ import annotations

from sitedoctor.checks import Finding
from sitedoctor.scoring import (
    category_score,
    grade,
    links_score,
    overall_score,
    score_page,
)


def test_category_score_penalties():
    findings = [
        Finding("seo", "error", "a", "m"),   # -15
        Finding("seo", "warn", "b", "m"),    # -6
        Finding("a11y", "info", "c", "m"),   # not seo
    ]
    assert category_score(findings, "seo") == 100 - 15 - 6
    assert category_score(findings, "a11y") == 100 - 1


def test_category_score_floor_zero():
    findings = [Finding("seo", "error", f"e{i}", "m") for i in range(10)]
    assert category_score(findings, "seo") == 0


def test_score_page_keys():
    s = score_page([])
    assert set(s) == {"seo", "a11y", "performance", "security"}
    assert all(v == 100 for v in s.values())


def test_links_score():
    assert links_score(0, 0) == 100
    assert links_score(10, 0) == 100
    assert links_score(10, 5) == 50
    assert links_score(4, 4) == 0


def test_overall_weighted():
    # all 100 -> 100
    assert overall_score(100, 100, 100, 100, 100) == 100.0
    # known weighted mix (seo, a11y, perf, security, links)
    assert overall_score(80, 60, 100, 90, 50) == round(
        80 * 0.25 + 60 * 0.25 + 100 * 0.15 + 90 * 0.15 + 50 * 0.20, 1)


def test_grade_bands():
    assert grade(95).startswith("A")
    assert grade(80).startswith("B")
    assert grade(65).startswith("C")
    assert grade(45).startswith("D")
    assert grade(10).startswith("F")
