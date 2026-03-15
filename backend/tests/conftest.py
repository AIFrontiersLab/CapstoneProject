"""Pytest fixtures."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Temporary directory for uploads."""
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def sample_txt_path(tmp_path):
    """Sample TXT file."""
    p = tmp_path / "sample.txt"
    p.write_text("Employee benefits start after 90 days. Health insurance begins the first day of the month following eligibility.")
    return p
