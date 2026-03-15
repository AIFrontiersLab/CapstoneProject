"""Document parsing for PDF, TXT, CSV, Excel."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber
from pypdf import PdfReader

from app.core.logging import get_logger
from app.utils.file import get_extension

logger = get_logger(__name__)


@dataclass
class ParsedPage:
    """Content from a single page or sheet."""

    content: str
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None


@dataclass
class ParseResult:
    """Result of parsing a document."""

    full_text: str
    pages: list[ParsedPage] = field(default_factory=list)
    page_count: Optional[int] = None
    sheet_names: Optional[list[str]] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and bool(self.full_text.strip())


class ParsingService:
    """Parse supported document types into unified text + metadata."""

    def parse_file(self, file_path: Path, file_name: str) -> ParseResult:
        """Dispatch by extension and return ParseResult."""
        ext = get_extension(file_name)
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        if ext == ".txt":
            return self._parse_txt(file_path)
        if ext == ".csv":
            return self._parse_csv(file_path)
        if ext == ".xlsx":
            return self._parse_xlsx(file_path)
        return ParseResult(
            full_text="",
            error=f"Unsupported file type: {ext}",
        )

    def _parse_pdf(self, path: Path) -> ParseResult:
        """Extract text from PDF using pdfplumber (better table handling)."""
        pages: list[ParsedPage] = []
        full_parts: list[str] = []
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        full_parts.append(text)
                        pages.append(ParsedPage(content=text, page_number=i))
                full_text = "\n\n".join(full_parts)
                return ParseResult(
                    full_text=full_text,
                    pages=pages,
                    page_count=len(pdf.pages),
                )
        except Exception as e:
            logger.exception("pdf_parse_error", path=str(path), error=str(e))
            return ParseResult(
                full_text="",
                pages=[],
                error=f"Failed to parse PDF: {e}",
            )

    def _parse_txt(self, path: Path) -> ParseResult:
        """Read plain text file."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return ParseResult(
                full_text=text,
                pages=[ParsedPage(content=text, page_number=1)],
                page_count=1,
            )
        except Exception as e:
            logger.exception("txt_parse_error", path=str(path), error=str(e))
            return ParseResult(full_text="", pages=[], error=str(e))

    def _parse_csv(self, path: Path) -> ParseResult:
        """Parse CSV with pandas; include headers and row context."""
        try:
            df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
            return self._dataframe_to_result(df, path.name, sheet_name=None)
        except Exception as e:
            logger.exception("csv_parse_error", path=str(path), error=str(e))
            return ParseResult(full_text="", pages=[], error=str(e))

    def _parse_xlsx(self, path: Path) -> ParseResult:
        """Parse Excel file; each sheet becomes a logical 'page'."""
        try:
            xl = pd.ExcelFile(path)
            sheet_names = xl.sheet_names
            all_pages: list[ParsedPage] = []
            full_parts: list[str] = []
            for sheet_name in sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name, header=0)
                result = self._dataframe_to_result(
                    df, path.name, sheet_name=sheet_name
                )
                full_parts.append(result.full_text)
                all_pages.extend(result.pages)
            full_text = "\n\n".join(full_parts)
            return ParseResult(
                full_text=full_text,
                pages=all_pages,
                sheet_names=sheet_names,
            )
        except Exception as e:
            logger.exception("xlsx_parse_error", path=str(path), error=str(e))
            return ParseResult(full_text="", pages=[], error=str(e))

    def _dataframe_to_result(
        self,
        df: pd.DataFrame,
        file_name: str,
        sheet_name: Optional[str] = None,
    ) -> ParseResult:
        """Convert DataFrame to text and ParsedPage list with row refs."""
        if df.empty:
            text = f"[Sheet: {sheet_name or 'default'}] (empty)"
            return ParseResult(
                full_text=text,
                pages=[ParsedPage(content=text, sheet_name=sheet_name)],
            )
        # Header row
        header = " | ".join(str(c) for c in df.columns)
        parts = [f"Columns: {header}"]
        chunk_size = 50
        pages: list[ParsedPage] = []
        for start in range(0, len(df), chunk_size):
            end = min(start + chunk_size, len(df))
            sub = df.iloc[start:end]
            rows_text = sub.to_string(index=False)
            content = f"Rows {start + 1}-{end}:\n{rows_text}"
            parts.append(content)
            pages.append(
                ParsedPage(
                    content=content,
                    sheet_name=sheet_name,
                    row_start=start + 1,
                    row_end=end,
                )
            )
        full_text = "\n\n".join(parts)
        return ParseResult(
            full_text=full_text,
            pages=pages,
            sheet_names=[sheet_name] if sheet_name else None,
        )
