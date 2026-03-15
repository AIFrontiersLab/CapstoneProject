"""Agent orchestrator: Planner -> Retriever -> Reasoner -> Validator with execution summary."""

from typing import Optional

from app.core.logging import get_logger
from app.schemas.query import (
    AgentQueryResponse,
    ExecutionSummary,
    QueryRequest,
    SupportStatus,
)
from app.agents.planner import PlannerAgent, Plan
from app.agents.retriever import RetrieverAgent
from app.agents.reasoner import ReasonerAgent
from app.agents.validator import ValidatorAgent, ValidationResult
from app.models.chunk import DocumentChunk
from app.rag.pipeline import _chunk_ref, _build_citations, _to_retrieved_chunks

logger = get_logger(__name__)


class AgentOrchestrator:
    """Runs the full agent workflow and returns structured response with execution summary."""

    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent()
        self.reasoner = ReasonerAgent()
        self.validator = ValidatorAgent()

    def query(self, request: QueryRequest) -> AgentQueryResponse:
        """Execute planner -> retriever -> reasoner -> validator."""
        question = request.question.strip()
        summary_steps: list[str] = []

        # 1. Plan
        plan = self.planner.plan(question)
        summary_steps.append(f"Planned query: {plan.planned_query[:80]}...")
        if plan.error:
            return AgentQueryResponse(
                question=question,
                answer="I cannot process this request. " + (plan.error or "Query rejected."),
                execution_summary=ExecutionSummary(
                    planned_query=plan.planned_query,
                    retrieval_performed=False,
                    chunks_retrieved=0,
                    validation_passed=False,
                    support_status=SupportStatus.INSUFFICIENT,
                    summary_steps=summary_steps,
                ),
                support_status=SupportStatus.INSUFFICIENT,
            )

        if not plan.needs_retrieval:
            return AgentQueryResponse(
                question=question,
                answer="No retrieval was planned for this question.",
                execution_summary=ExecutionSummary(
                    planned_query=plan.planned_query,
                    retrieval_performed=False,
                    chunks_retrieved=0,
                    validation_passed=False,
                    support_status=SupportStatus.INSUFFICIENT,
                    summary_steps=summary_steps,
                ),
                support_status=SupportStatus.INSUFFICIENT,
            )

        # 2. Retrieve
        chunks_with_scores = self.retriever.retrieve(plan.planned_query)
        chunks = [c for c, _ in chunks_with_scores]
        scores = [s for _, s in chunks_with_scores]
        summary_steps.append(f"Retrieved {len(chunks)} relevant chunks.")
        if not chunks:
            return AgentQueryResponse(
                question=question,
                answer="I could not find enough evidence in the uploaded documents to answer this confidently. Please upload relevant documents first.",
                retrieved_chunks=[],
                execution_summary=ExecutionSummary(
                    planned_query=plan.planned_query,
                    retrieval_performed=True,
                    chunks_retrieved=0,
                    validation_passed=False,
                    support_status=SupportStatus.INSUFFICIENT,
                    summary_steps=summary_steps,
                ),
                support_status=SupportStatus.INSUFFICIENT,
            )

        # 3. Reason
        answer = self.reasoner.synthesize(question, chunks_with_scores)
        summary_steps.append("Generated answer from retrieved context.")

        # 4. Validate
        validation = self.validator.validate(answer, chunks_with_scores, question)
        summary_steps.append(validation.summary)

        citations = _build_citations(chunks)
        return AgentQueryResponse(
            question=question,
            answer=answer,
            citations=citations,
            retrieved_chunks=_to_retrieved_chunks(chunks, scores),
            execution_summary=ExecutionSummary(
                planned_query=plan.planned_query,
                retrieval_performed=True,
                chunks_retrieved=len(chunks),
                validation_passed=validation.passed,
                support_status=validation.support_status,
                summary_steps=summary_steps,
            ),
            support_status=validation.support_status,
            confidence_note=validation.summary if validation.issues else None,
        )


_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator
