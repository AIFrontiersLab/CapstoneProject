# API Reference

Base URL: `/api/v1` (e.g. `http://localhost:8000/api/v1`).

## Health

### GET /health

Liveness/readiness check.

**Response** (200):

```json
{
  "status": "ok",
  "service": "enterprise-genai-rag"
}
```

---

## Documents

### POST /documents/upload

Upload a document for parsing, chunking, embedding, and indexing.

**Request**: `multipart/form-data` with field `file` (PDF, TXT, CSV, or XLSX).

**Success** (200):

```json
{
  "document_id": "uuid",
  "file_name": "policy.pdf",
  "status": "completed",
  "message": "Document uploaded and indexed successfully.",
  "chunk_count": 12
}
```

**Errors**:

- 400: Unsupported file type or validation failure.
- 413: File too large (max configured in `MAX_FILE_SIZE_MB`).
- 422: Ingestion failed (e.g. parse error).

---

### GET /documents

List all uploaded documents.

**Response** (200): Array of:

```json
{
  "document_id": "uuid",
  "file_name": "policy.pdf",
  "file_type": ".pdf",
  "status": "completed",
  "created_at": "2025-03-14T12:00:00",
  "chunk_count": 12
}
```

---

### GET /documents/{document_id}

Get metadata for one document.

**Response** (200): Same shape as list item plus `file_size_bytes`, `page_count`, `sheet_names`, `error_message` if any.

**Errors**: 404 if not found.

---

## Query

### POST /query

Standard RAG: retrieve top-k chunks and generate answer.

**Request**:

```json
{
  "question": "What is the eligibility period for benefits?"
}
```

**Response** (200):

```json
{
  "question": "What is the eligibility period for benefits?",
  "answer": "According to the uploaded policy document, employees are eligible after 90 days...",
  "citations": [
    {
      "source_file": "policy.pdf",
      "page": 12,
      "sheet_name": null,
      "excerpt": "...",
      "chunk_id": "..."
    }
  ],
  "retrieved_chunks": [
    {
      "content": "...",
      "metadata": { "document_id": "...", "file_name": "...", "page": 12 },
      "score": 0.85,
      "chunk_id": "..."
    }
  ],
  "execution_summary": null,
  "support_status": "supported",
  "confidence_note": null
}
```

`support_status`: `"supported"` | `"partial"` | `"insufficient"`.

---

### POST /agents/query

Agent workflow: Planner → Retriever → Reasoner → Validator. Same request/response shape as `/query`, plus a non-null `execution_summary`:

```json
{
  "question": "...",
  "answer": "...",
  "citations": [...],
  "retrieved_chunks": [...],
  "execution_summary": {
    "planned_query": "...",
    "retrieval_performed": true,
    "chunks_retrieved": 5,
    "validation_passed": true,
    "support_status": "supported",
    "summary_steps": [
      "Planned query: ...",
      "Retrieved 5 relevant chunks.",
      "Generated answer from retrieved context.",
      "Answer appears grounded in retrieved sources with citations."
    ]
  },
  "support_status": "supported",
  "confidence_note": null
}
```

**Errors** (422): Validation error if body is invalid (e.g. missing `question`).
