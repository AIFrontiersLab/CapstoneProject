"""Document-related Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentIngestionStatus(str, Enum):
    """Status of document ingestion pipeline."""

    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """Metadata for a single document (file-level)."""

    document_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    page_count: Optional[int] = None
    sheet_names: Optional[list[str]] = None
    created_at: datetime
    status: DocumentIngestionStatus
    error_message: Optional[str] = None
    chunk_count: int = 0


class DocumentListItem(BaseModel):
    """Summary for document list API."""

    document_id: str
    file_name: str
    file_type: str
    status: DocumentIngestionStatus
    created_at: datetime
    chunk_count: int = 0


class DocumentDetail(DocumentMetadata):
    """Full document detail (same as metadata for now)."""

    pass


class UploadResponse(BaseModel):
    """Response after document upload."""

    document_id: str
    file_name: str
    status: DocumentIngestionStatus
    message: str
    chunk_count: int = 0
