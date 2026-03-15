"""Query and RAG response schemas."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SupportStatus(str, Enum):
    """Whether the answer is supported by retrieved evidence."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class Citation(BaseModel):
    """A single citation pointing to a source chunk."""

    source_file: str
    page: Optional[int] = None
    sheet_name: Optional[str] = None
    excerpt: Optional[str] = None
    chunk_id: Optional[str] = None


class RetrievedChunk(BaseModel):
    """A chunk returned from vector search."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None
    chunk_id: Optional[str] = None


class ExecutionSummary(BaseModel):
    """Safe execution trace for agent workflow (no raw chain-of-thought)."""

    planned_query: Optional[str] = None
    retrieval_performed: bool = False
    chunks_retrieved: int = 0
    validation_passed: bool = False
    support_status: SupportStatus = SupportStatus.INSUFFICIENT
    summary_steps: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Request for standard RAG query."""

    question: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    """Response from RAG or agent query."""

    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    execution_summary: Optional[ExecutionSummary] = None
    support_status: SupportStatus = SupportStatus.INSUFFICIENT
    confidence_note: Optional[str] = None


class AgentQueryRequest(BaseModel):
    """Request for agent-based query (same as query for now)."""

    question: str = Field(..., min_length=1, max_length=2000)


class AgentQueryResponse(QueryResponse):
    """Response from agent workflow (includes execution summary)."""

    execution_summary: Optional[ExecutionSummary] = None
