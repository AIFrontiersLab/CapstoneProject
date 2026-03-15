"""Document upload and list API."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.db.metadata_store import get_metadata_store
from app.schemas.document import (
    DocumentDetail,
    DocumentIngestionStatus,
    DocumentListItem,
    UploadResponse,
)
from app.services.ingestion import get_ingestion_service
from app.services.vector_store import get_vector_store
from app.utils.file import allowed_file_type

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a single document. Validates type/size, then parses, chunks, embeds, and indexes."""
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb} MB.",
        )
    if not allowed_file_type(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: .pdf, .txt, .csv, .xlsx",
        )
    ingestion = get_ingestion_service()
    path, err = ingestion.validate_and_store_upload(content, file.filename or "unknown")
    if err:
        raise HTTPException(status_code=400, detail=err)
    assert path is not None
    try:
        doc_id, status, chunk_count, error_msg = ingestion.ingest_file(path, file.filename or "unknown")
        if status == DocumentIngestionStatus.FAILED:
            raise HTTPException(
                status_code=422,
                detail=error_msg or "Ingestion failed",
            )
        return UploadResponse(
            document_id=doc_id,
            file_name=file.filename or "unknown",
            status=status,
            message="Document uploaded and indexed successfully.",
            chunk_count=chunk_count,
        )
    finally:
        if path.exists():
            path.unlink(missing_ok=True)


@router.get("", response_model=list[DocumentListItem])
def list_documents():
    """List all uploaded documents with status."""
    store = get_metadata_store()
    docs = store.list_all()
    return [
        DocumentListItem(
            document_id=d.document_id,
            file_name=d.file_name,
            file_type=d.file_type,
            status=d.status,
            created_at=d.created_at,
            chunk_count=d.chunk_count,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str):
    """Get document metadata by ID."""
    store = get_metadata_store()
    doc = store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetail(
        document_id=doc.document_id,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        sheet_names=doc.sheet_names,
        created_at=doc.created_at,
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
    )
