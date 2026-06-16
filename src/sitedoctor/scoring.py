"""Turn findings into 0-100 scores. Pure and unit-testable."""

from __future__ import annotations

from .checks import Finding

SEVERITY_PENALTY = {"error": 15, "warn": 6, "info": 1}

WEIGHTS = {"seo": 0.30, "a11y": 0.30, "performance": 0.20, "links": 0.20}


def category_score(findings: list[Finding], category: str) -> int:
    penalty = sum(SEVERITY_PENALTY[f.severity] for f in findings if f.category == category)
    return max(0, 100 - penalty)


def score_page(findings: list[Finding]) -> dict[str, int]:
    return {c: category_score(findings, c) for c in ("seo", "a11y", "performance")}


def links_score(total_checked: int, broken: int) -> int:
    if total_checked <= 0:
        return 100
    return round(100 * (1 - broken / total_checked))


def overall_score(seo: float, a11y: float, perf: float, links: float) -> float:
    return round(
        seo * WEIGHTS["seo"]
        + a11y * WEIGHTS["a11y"]
        + perf * WEIGHTS["performance"]
        + links * WEIGHTS["links"],
        1,
    )


def grade(score: float) -> str:
    for threshold, label in [
        (90, "A — healthy"),
        (75, "B — good"),
        (60, "C — needs work"),
        (40, "D — poor"),
        (0, "F — critical"),
    ]:
        if score >= threshold:
            return label
    return "F — critical"
