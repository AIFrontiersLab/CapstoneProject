"""Tests for chunking service."""

from app.services.chunking import ChunkingService
from app.services.parsing import ParseResult, ParsedPage


def test_chunk_parse_result():
    parse_result = ParseResult(
        full_text="First page content here. " * 50,
        pages=[ParsedPage(content="First page content here. " * 50, page_number=1)],
    )
    svc = ChunkingService(chunk_size=200, chunk_overlap=50)
    chunks = svc.chunk_parse_result(parse_result, "doc-1", "test.pdf")
    assert len(chunks) >= 1
    assert all(c.metadata.document_id == "doc-1" for c in chunks)
    assert all(c.metadata.file_name == "test.pdf" for c in chunks)


def test_chunk_empty():
    parse_result = ParseResult(full_text="", pages=[])
    svc = ChunkingService()
    chunks = svc.chunk_parse_result(parse_result, "doc-1", "empty.txt")
    assert chunks == []
