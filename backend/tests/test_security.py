"""Tests for security and guardrails."""

from app.utils.security import is_safe_query, sanitize_for_prompt


def test_is_safe_query_valid():
    ok, err = is_safe_query("What are the benefits?")
    assert ok is True
    assert err is None


def test_is_safe_query_empty():
    ok, err = is_safe_query("")
    assert ok is False
    assert err is not None


def test_sanitize_for_prompt_truncate():
    long = "a" * 100000
    out = sanitize_for_prompt(long, max_length=100)
    assert len(out) <= 120  # 100 + truncation message


def test_sanitize_empty():
    assert sanitize_for_prompt("") == ""
    assert sanitize_for_prompt("   ") == ""
