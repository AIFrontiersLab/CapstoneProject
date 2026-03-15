"""Internal data models (non-Pydantic) for services."""

from .chunk import DocumentChunk, ChunkMetadata

__all__ = ["DocumentChunk", "ChunkMetadata"]
