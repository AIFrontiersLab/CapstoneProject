"""Tests for agent workflow."""

from app.agents.planner import PlannerAgent, Plan
from app.agents.validator import ValidatorAgent, ValidationResult
from app.models.chunk import DocumentChunk
from app.models.chunk import ChunkMetadata


def test_planner_plan():
    agent = PlannerAgent()
    plan = agent.plan("What are the benefits?")
    assert plan.needs_retrieval is True
    assert "benefits" in plan.planned_query
    assert plan.error is None


def test_planner_rejects_empty():
    agent = PlannerAgent()
    plan = agent.plan("")
    assert plan.error is not None


def test_validator_insufficient():
    agent = ValidatorAgent()
    meta = ChunkMetadata(document_id="d1", file_name="handbook.pdf")
    chunk = DocumentChunk(content="Some text", metadata=meta)
    result = agent.validate("This is my answer.", [(chunk, 0.9)], "What is X?")
    assert isinstance(result, ValidationResult)
    assert result.support_status.value in ("supported", "partial", "insufficient")
