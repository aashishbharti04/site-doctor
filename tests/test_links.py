"""Tests for link classification (pure)."""

from __future__ import annotations

from sitedoctor.links import classify


def test_ok_statuses():
    assert classify(200) == "ok"
    assert classify(301) == "ok"
    assert classify(399) == "ok"


def test_broken_statuses():
    assert classify(404) == "broken"
    assert classify(410) == "broken"
    assert classify(500) == "broken"
    assert classify(503) == "broken"


def test_blocked_statuses_not_broken():
    # bot-protection / WAF responses — common for LinkedIn (999), social sites
    for s in (401, 403, 405, 429, 999):
        assert classify(s) == "blocked"


def test_connection_error_is_unreachable():
    assert classify(0) == "unreachable"
