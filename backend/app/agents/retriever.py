"""Retriever Agent: fetch relevant chunks from vector store."""

from typing import List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chunk import DocumentChunk
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)


class RetrieverAgent:
    """Fetches top-k relevant chunks for a query."""

    def __init__(self) -> None:
        self.vector_store = get_vector_store()
        self.top_k = get_settings().top_k_retrieve

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[tuple[DocumentChunk, float]]:
        """Return list of (chunk, score) for the query."""
        k = top_k or self.top_k
        results = self.vector_store.search(query, top_k=k)
        logger.info("retriever_agent", query_preview=query[:50], chunks=len(results))
        return results
