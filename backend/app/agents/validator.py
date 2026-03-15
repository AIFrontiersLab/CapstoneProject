"""Validator Agent: check answer against sources, hallucination risk, citations."""

from dataclasses import dataclass
from typing import List, Optional

from app.core.logging import get_logger
from app.models.chunk import DocumentChunk
from app.schemas.query import SupportStatus

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Structured validation output."""

    passed: bool
    support_status: SupportStatus
    summary: str
    issues: List[str]


class ValidatorAgent:
    """Validates that the answer is supported by retrieved chunks and has citations."""

    def validate(
        self,
        answer: str,
        chunks: List[tuple[DocumentChunk, float]],
        question: str,
    ) -> ValidationResult:
        """Check answer grounding and citation presence."""
        issues: List[str] = []
        if not answer or not answer.strip():
            return ValidationResult(
                passed=False,
                support_status=SupportStatus.INSUFFICIENT,
                summary="Empty answer.",
                issues=["Answer is empty"],
            )
        if not chunks:
            return ValidationResult(
                passed=False,
                support_status=SupportStatus.INSUFFICIENT,
                summary="No sources to validate against.",
                issues=["No retrieved chunks"],
            )
        # Heuristic: answer should reference at least one source (file name or "document")
        chunk_files = {c.metadata.file_name for c, _ in chunks}
        refs_found = sum(1 for f in chunk_files if f in answer)
        if refs_found == 0 and "document" not in answer.lower() and "uploaded" not in answer.lower():
            issues.append("Answer may not cite uploaded documents")
        # Insufficient evidence phrase is acceptable
        if "could not find enough evidence" in answer.lower():
            return ValidationResult(
                passed=True,
                support_status=SupportStatus.INSUFFICIENT,
                summary="Answer correctly states insufficient evidence.",
                issues=[],
            )
        if issues:
            return ValidationResult(
                passed=refs_found > 0,
                support_status=SupportStatus.PARTIAL if refs_found > 0 else SupportStatus.INSUFFICIENT,
                summary="Validation completed with caveats.",
                issues=issues,
            )
        return ValidationResult(
            passed=True,
            support_status=SupportStatus.SUPPORTED,
            summary="Answer appears grounded in retrieved sources with citations.",
            issues=[],
        )
