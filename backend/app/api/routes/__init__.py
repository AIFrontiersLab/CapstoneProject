"""API route modules."""

from .documents import router as documents_router
from .query import router as query_router
from .health import router as health_router

__all__ = ["documents_router", "query_router", "health_router"]
