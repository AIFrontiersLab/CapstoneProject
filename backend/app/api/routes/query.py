"""Query API: standard RAG and agent-based query."""

from fastapi import APIRouter, HTTPException

from app.schemas.query import AgentQueryRequest, AgentQueryResponse, QueryRequest, QueryResponse
from app.rag.pipeline import get_rag_service
from app.agents.orchestrator import get_agent_orchestrator

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Standard RAG pipeline: retrieve top-k chunks and generate answer."""
    rag = get_rag_service()
    return rag.query(request.question)


@router.post("/agents/query", response_model=AgentQueryResponse)
def agents_query(request: AgentQueryRequest):
    """Agent-based query: planner -> retriever -> reasoner -> validator with execution summary."""
    orchestrator = get_agent_orchestrator()
    return orchestrator.query(QueryRequest(question=request.question))
