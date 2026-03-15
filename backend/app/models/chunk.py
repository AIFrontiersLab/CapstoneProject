"""Internal chunk model for RAG pipeline."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChunkMetadata:
    """Metadata attached to a text chunk."""

    document_id: str
    file_name: str
    page: Optional[int] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for vector store and API."""
        d: dict[str, Any] = {
            "document_id": self.document_id,
            "file_name": self.file_name,
        }
        if self.page is not None:
            d["page"] = self.page
        if self.sheet_name is not None:
            d["sheet_name"] = self.sheet_name
        if self.row_start is not None:
            d["row_start"] = self.row_start
        if self.row_end is not None:
            d["row_end"] = self.row_end
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChunkMetadata":
        """Create from dict (e.g. from vector store)."""
        extra = {k: v for k, v in d.items() if k not in (
            "document_id", "file_name", "page", "sheet_name", "row_start", "row_end"
        )}
        return cls(
            document_id=d.get("document_id", ""),
            file_name=d.get("file_name", ""),
            page=d.get("page"),
            sheet_name=d.get("sheet_name"),
            row_start=d.get("row_start"),
            row_end=d.get("row_end"),
            extra=extra,
        )


@dataclass
class DocumentChunk:
    """A single chunk of document text with metadata."""

    content: str
    metadata: ChunkMetadata
    chunk_id: Optional[str] = None
