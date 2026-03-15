"""Document ingestion pipeline: upload -> parse -> chunk -> embed -> index."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.metadata_store import get_metadata_store
from app.schemas.document import DocumentIngestionStatus, DocumentMetadata
from app.services.parsing import ParsingService
from app.services.chunking import ChunkingService
from app.services.embedding import get_embedding_service
from app.services.vector_store import get_vector_store
from app.utils.file import allowed_file_type

logger = get_logger(__name__)


class IngestionService:
    """Orchestrate full ingestion pipeline and metadata updates."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.parsing = ParsingService()
        self.chunking = ChunkingService()
        self.metadata_store = get_metadata_store()
        self.vector_store = get_vector_store()
        self.embedding = get_embedding_service()

    def ingest_file(self, file_path: Path, file_name: str) -> Tuple[str, DocumentIngestionStatus, int, Optional[str]]:
        """
        Ingest a single file. Returns (document_id, status, chunk_count, error_message).
        """
        document_id = str(uuid.uuid4())
        meta = DocumentMetadata(
            document_id=document_id,
            file_name=file_name,
            file_type=Path(file_name).suffix.lower(),
            file_size_bytes=file_path.stat().st_size,
            created_at=datetime.utcnow(),
            status=DocumentIngestionStatus.PENDING,
            chunk_count=0,
        )
        self.metadata_store.upsert(meta)

        try:
            # Parse
            self.metadata_store.update_status(document_id, DocumentIngestionStatus.PARSING)
            parse_result = self.parsing.parse_file(file_path, file_name)
            if not parse_result.success:
                self.metadata_store.update_status(
                    document_id,
                    DocumentIngestionStatus.FAILED,
                    error_message=parse_result.error or "Parse failed",
                )
                return document_id, DocumentIngestionStatus.FAILED, 0, parse_result.error

            # Chunk
            self.metadata_store.update_status(document_id, DocumentIngestionStatus.CHUNKING)
            chunks = self.chunking.chunk_parse_result(parse_result, document_id, file_name)
            if not chunks:
                self.metadata_store.update_status(
                    document_id,
                    DocumentIngestionStatus.FAILED,
                    error_message="No chunks produced",
                )
                return document_id, DocumentIngestionStatus.FAILED, 0, "No chunks produced"

            # Embed & index
            self.metadata_store.update_status(document_id, DocumentIngestionStatus.EMBEDDING)
            self.vector_store.add_chunks(chunks)
            self.metadata_store.update_status(
                document_id,
                DocumentIngestionStatus.COMPLETED,
                chunk_count=len(chunks),
            )
            meta.page_count = parse_result.page_count
            meta.sheet_names = parse_result.sheet_names
            meta.chunk_count = len(chunks)
            meta.status = DocumentIngestionStatus.COMPLETED
            self.metadata_store.upsert(meta)
            logger.info("ingestion_completed", document_id=document_id, chunks=len(chunks))
            return document_id, DocumentIngestionStatus.COMPLETED, len(chunks), None
        except Exception as e:
            logger.exception("ingestion_failed", document_id=document_id, error=str(e))
            self.metadata_store.update_status(
                document_id,
                DocumentIngestionStatus.FAILED,
                error_message=str(e),
            )
            return document_id, DocumentIngestionStatus.FAILED, 0, str(e)

    def validate_and_store_upload(self, content: bytes, filename: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Validate file and write to upload dir. Returns (path, error).
        """
        if not allowed_file_type(filename):
            return None, f"Unsupported file type. Allowed: .pdf, .txt, .csv, .xlsx"
        if len(content) > self.settings.max_file_size_bytes:
            return None, f"File too large. Max {self.settings.max_file_size_mb} MB"
        if len(content.strip()) == 0:
            return None, "File is empty"
        self.settings.ensure_dirs()
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        path = self.settings.upload_dir / safe_name
        path.write_bytes(content)
        return path, None


_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
