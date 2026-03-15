"""File validation and path utilities."""

from pathlib import Path
from typing import Optional

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".xlsx"}
ALLOWED_MIME_EXTENSION_MAP = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}


def get_extension(filename: str) -> str:
    """Return lowercase extension including dot, e.g. '.pdf'."""
    return Path(filename).suffix.lower()


def allowed_file_type(filename: str, content_type: Optional[str] = None) -> bool:
    """Check if file is allowed by extension and optionally by content type."""
    ext = get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if content_type and content_type in ALLOWED_MIME_EXTENSION_MAP:
        expected_ext = ALLOWED_MIME_EXTENSION_MAP[content_type]
        if ext != expected_ext:
            return False
    return True
