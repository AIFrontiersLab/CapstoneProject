"""Tests for document parsing service."""

import pytest
from pathlib import Path

from app.services.parsing import ParsingService, ParseResult


def test_parse_txt(tmp_path):
    path = tmp_path / "test.txt"
    path.write_text("Hello world.\n\nSecond paragraph.")
    svc = ParsingService()
    result = svc.parse_file(path, "test.txt")
    assert result.success
    assert "Hello world" in result.full_text
    assert result.page_count == 1


def test_parse_txt_empty(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("")
    svc = ParsingService()
    result = svc.parse_file(path, "empty.txt")
    assert not result.success
    assert result.full_text == ""


def test_parse_unsupported(tmp_path):
    path = tmp_path / "file.xyz"
    path.write_text("data")
    svc = ParsingService()
    result = svc.parse_file(path, "file.xyz")
    assert not result.success
    assert "Unsupported" in (result.error or "")
