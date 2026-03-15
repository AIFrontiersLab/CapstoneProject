"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Liveness/readiness check."""
    return {"status": "ok", "service": "enterprise-genai-rag"}
