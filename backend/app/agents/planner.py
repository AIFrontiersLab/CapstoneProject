"""Planner Agent: interpret question, decide if retrieval needed, plan steps."""

from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger
from app.utils.security import is_safe_query

logger = get_logger(__name__)


@dataclass
class Plan:
    """Structured output from planner."""

    needs_retrieval: bool
    planned_query: str
    reasoning_summary: str
    error: Optional[str] = None


class PlannerAgent:
    """Interprets user question and decides retrieval strategy."""

    def plan(self, question: str) -> Plan:
        """Produce a plan for answering the question."""
        safe, err = is_safe_query(question)
        if not safe:
            return Plan(
                needs_retrieval=False,
                planned_query=question,
                reasoning_summary="Query rejected by safety check.",
                error=err,
            )
        # For this capstone we always do retrieval for document Q&A
        normalized = question.strip()
        return Plan(
            needs_retrieval=True,
            planned_query=normalized,
            reasoning_summary="Document Q&A: will retrieve relevant chunks and generate grounded answer.",
        )
