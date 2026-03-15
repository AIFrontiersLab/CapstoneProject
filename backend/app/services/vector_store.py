"""Vector store service using ChromaDB with abstraction for future backends."""

from typing import Any, List, Optional
import uuid

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chunk import DocumentChunk
from app.services.embedding import get_embedding_service

logger = get_logger(__name__)

COLLECTION_NAME = "enterprise_rag_chunks"


class VectorStoreService:
    """ChromaDB-backed vector store with metadata filtering."""

    def __init__(self) -> None:
        settings = get_settings()
        self.persist_dir = str(settings.chroma_persist_dir)
        self._client = None
        self._collection = None
        self._embedding = get_embedding_service()
        self.top_k = settings.top_k_retrieve
        self.min_score = settings.min_relevance_score

    def _get_client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "RAG document chunks"},
            )
        return self._collection

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """Add chunks to the vector store. Compute embeddings if not provided."""
        if not chunks:
            return
        ids = [c.chunk_id or str(uuid.uuid4()) for c in chunks]
        texts = [c.content for c in chunks]
        metadatas = [c.metadata.to_dict() for c in chunks]
        # ChromaDB metadata values must be str, int, float, bool
        for m in metadatas:
            for k, v in list(m.items()):
                if v is None:
                    del m[k]
                elif isinstance(v, list):
                    m[k] = str(v)
                elif not isinstance(v, (str, int, float, bool)):
                    m[k] = str(v)
        if embeddings is None:
            embeddings = self._embedding.embed_documents(texts)
        coll = self._get_collection()
        coll.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        logger.info("vector_store_added", count=len(chunks), doc_ids=list({c.metadata.document_id for c in chunks}))

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> List[tuple[DocumentChunk, float]]:
        """
        Semantic search. Returns list of (DocumentChunk, score).
        Chroma returns distance; we convert to similarity-like score (lower distance = higher score).
        """
        k = top_k or self.top_k
        coll = self._get_collection()
        query_embedding = self._embedding.embed_query(query)
        where = None
        if filter_metadata:
            where = filter_metadata  # Chroma where clause
        result = coll.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        if not result["ids"] or not result["ids"][0]:
            return []
        chunks_with_scores: List[tuple[DocumentChunk, float]] = []
        for i, doc_id in enumerate(result["ids"][0]):
            doc = result["documents"][0][i] if result["documents"] else ""
            meta = result["metadatas"][0][i] if result["metadatas"] else {}
            dist = result["distances"][0][i] if result.get("distances") else 0.0
            # Chroma L2 distance: lower is better. Convert to score in [0,1]: 1 / (1 + distance)
            score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
            if score < self.min_score:
                continue
            from app.models.chunk import ChunkMetadata
            metadata = ChunkMetadata.from_dict(meta)
            chunk = DocumentChunk(content=doc, metadata=metadata, chunk_id=doc_id)
            chunks_with_scores.append((chunk, score))
        return chunks_with_scores

    def delete_by_document_id(self, document_id: str) -> int:
        """Remove all chunks for a document. Returns count deleted."""
        coll = self._get_collection()
        try:
            existing = coll.get(where={"document_id": document_id})
            if existing and existing["ids"]:
                coll.delete(ids=existing["ids"])
                return len(existing["ids"])
        except Exception as e:
            logger.warning("vector_store_delete_error", document_id=document_id, error=str(e))
        return 0

    def count(self) -> int:
        """Total number of chunks in the collection."""
        coll = self._get_collection()
        return coll.count()


_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
