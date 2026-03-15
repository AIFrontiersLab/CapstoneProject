"""Chunking service: recursive split with overlap and metadata preservation."""

import re
from typing import Optional

from app.models.chunk import ChunkMetadata, DocumentChunk
from app.services.parsing import ParseResult, ParsedPage
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChunkingService:
    """Split document text into semantically useful chunks with metadata."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_parse_result(
        self,
        parse_result: ParseResult,
        document_id: str,
        file_name: str,
    ) -> list[DocumentChunk]:
        """
        Chunk a ParseResult while preserving page/sheet/row metadata.
        If the parser provided pages, we chunk within each page and attach metadata.
        """
        if not parse_result.full_text.strip():
            return []

        chunks: list[DocumentChunk] = []
        if parse_result.pages:
            for page in parse_result.pages:
                page_chunks = self._chunk_text(
                    page.content,
                    document_id=document_id,
                    file_name=file_name,
                    page_number=page.page_number,
                    sheet_name=page.sheet_name,
                    row_start=page.row_start,
                    row_end=page.row_end,
                )
                chunks.extend(page_chunks)
        else:
            chunks = self._chunk_text(
                parse_result.full_text,
                document_id=document_id,
                file_name=file_name,
            )

        for i, c in enumerate(chunks):
            if not c.chunk_id:
                c.chunk_id = f"{document_id}_{i}"
        return chunks

    def _chunk_text(
        self,
        text: str,
        document_id: str,
        file_name: str,
        page_number: Optional[int] = None,
        sheet_name: Optional[str] = None,
        row_start: Optional[int] = None,
        row_end: Optional[int] = None,
    ) -> list[DocumentChunk]:
        """Split text with overlap; one metadata for all chunks from same page/sheet."""
        cleaned = self._clean_text(text)
        if not cleaned:
            return []

        metadata = ChunkMetadata(
            document_id=document_id,
            file_name=file_name,
            page=page_number,
            sheet_name=sheet_name,
            row_start=row_start,
            row_end=row_end,
        )
        segments = self._split_recursive(cleaned, self.chunk_size, self.chunk_overlap)
        return [
            DocumentChunk(content=seg, metadata=metadata)
            for seg in segments
            if seg.strip()
        ]

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize whitespace and remove null bytes."""
        if not text:
            return ""
        text = text.replace("\x00", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _split_recursive(
        self,
        text: str,
        size: int,
        overlap: int,
    ) -> list[str]:
        """Split by size with overlap; break on paragraph/sentence when possible."""
        if len(text) <= size:
            return [text] if text.strip() else []

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + size
            if end >= len(text):
                chunk = text[start:]
                if chunk.strip():
                    chunks.append(chunk)
                break
            # Try to break at newline or sentence end
            segment = text[start:end]
            break_at = -1
            for sep in ("\n\n", "\n", ". "):
                idx = segment.rfind(sep)
                if idx > size // 2:
                    break_at = idx + len(sep)
                    break
            if break_at > 0:
                chunk = text[start : start + break_at]
                start = start + break_at - overlap
            else:
                chunk = text[start:end]
                start = end - overlap
            if chunk.strip():
                chunks.append(chunk)
        return chunks
