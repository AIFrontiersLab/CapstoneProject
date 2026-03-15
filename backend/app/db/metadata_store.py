"""SQLite-backed metadata store for documents."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from app.schemas.document import DocumentIngestionStatus, DocumentMetadata
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetadataStore:
    """Persist document metadata in SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        settings = get_settings()
        self.db_path = db_path or settings.sqlite_path
        if self.db_path:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    page_count INTEGER,
                    sheet_names TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    chunk_count INTEGER DEFAULT 0
                )
            """)

    def upsert(self, meta: DocumentMetadata) -> None:
        """Insert or update document metadata."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    document_id, file_name, file_type, file_size_bytes,
                    page_count, sheet_names, created_at, status, error_message, chunk_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    file_name=excluded.file_name,
                    file_type=excluded.file_type,
                    file_size_bytes=excluded.file_size_bytes,
                    page_count=excluded.page_count,
                    sheet_names=excluded.sheet_names,
                    status=excluded.status,
                    error_message=excluded.error_message,
                    chunk_count=excluded.chunk_count
                """,
                (
                    meta.document_id,
                    meta.file_name,
                    meta.file_type,
                    meta.file_size_bytes,
                    meta.page_count,
                    json.dumps(meta.sheet_names) if meta.sheet_names else None,
                    meta.created_at.isoformat(),
                    meta.status.value,
                    meta.error_message,
                    meta.chunk_count,
                ),
            )
        logger.info("metadata_upserted", document_id=meta.document_id, status=meta.status.value)

    def get(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_metadata(dict(row))

    def list_all(self) -> list[DocumentMetadata]:
        """List all documents."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_metadata(dict(r)) for r in rows]

    def update_status(
        self,
        document_id: str,
        status: DocumentIngestionStatus,
        error_message: Optional[str] = None,
        chunk_count: Optional[int] = None,
    ) -> None:
        """Update status and optionally chunk_count."""
        with self._conn() as conn:
            if chunk_count is not None:
                conn.execute(
                    "UPDATE documents SET status=?, error_message=?, chunk_count=? WHERE document_id=?",
                    (status.value, error_message, chunk_count, document_id),
                )
            else:
                conn.execute(
                    "UPDATE documents SET status=?, error_message=? WHERE document_id=?",
                    (status.value, error_message, document_id),
                )

    def delete(self, document_id: str) -> bool:
        """Delete document metadata. Returns True if a row was deleted."""
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
            return cur.rowcount > 0

    @staticmethod
    def _row_to_metadata(row: dict) -> DocumentMetadata:
        from datetime import datetime

        sheet_names = row.get("sheet_names")
        if isinstance(sheet_names, str):
            try:
                sheet_names = json.loads(sheet_names)
            except Exception:
                sheet_names = None
        return DocumentMetadata(
            document_id=row["document_id"],
            file_name=row["file_name"],
            file_type=row["file_type"],
            file_size_bytes=row["file_size_bytes"],
            page_count=row.get("page_count"),
            sheet_names=sheet_names,
            created_at=datetime.fromisoformat(row["created_at"]),
            status=DocumentIngestionStatus(row["status"]),
            error_message=row.get("error_message"),
            chunk_count=row.get("chunk_count") or 0,
        )


_metadata_store: Optional[MetadataStore] = None


def get_metadata_store() -> MetadataStore:
    """Return singleton metadata store."""
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = MetadataStore()
    return _metadata_store
