"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_list_documents_empty():
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_query_empty_body():
    r = client.post("/api/v1/query", json={})
    assert r.status_code == 422  # validation error


def test_query_valid():
    r = client.post("/api/v1/query", json={"question": "What is the policy?"})
    # May 200 (has chunks) or 200 with "could not find" answer (no docs)
    assert r.status_code == 200
    data = r.json()
    assert "question" in data
    assert "answer" in data


def test_agents_query_valid():
    r = client.post("/api/v1/agents/query", json={"question": "Summarize benefits."})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "execution_summary" in data
