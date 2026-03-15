"""Security and guardrail utilities: prompt injection mitigation, safe query check."""

import re
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns that may indicate prompt injection in retrieved text
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions", re.I),
    re.compile(r"disregard\s+(previous|above|all)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\|[a-z_]+\|>", re.I),  # special tokens
]


def sanitize_for_prompt(text: str, max_length: Optional[int] = 50000) -> str:
    """
    Sanitize retrieved document text before inserting into prompts.
    - Truncate if too long
    - Optionally redact obvious injection attempts (replace with placeholder)
    """
    if not text or not text.strip():
        return ""
    out = text.strip()
    for pat in INJECTION_PATTERNS:
        if pat.search(out):
            logger.warning("potential_injection_redacted", pattern=pat.pattern[:50])
            out = pat.sub("[REDACTED]", out)
    if max_length and len(out) > max_length:
        out = out[:max_length] + "\n[... truncated ...]"
    return out


def is_safe_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Basic safety check for user query. Returns (True, None) if safe,
    (False, reason) if potentially harmful or out-of-scope.
    """
    q = (query or "").strip()
    if not q:
        return False, "Empty query"
    if len(q) > 4000:
        return False, "Query too long"
    # Refuse obvious jailbreak attempts
    for pat in INJECTION_PATTERNS:
        if pat.search(q):
            return False, "Query contains disallowed patterns"
    return True, None
