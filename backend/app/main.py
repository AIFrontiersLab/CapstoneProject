"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api.routes import documents_router, query_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure data dirs exist on startup."""
    settings = get_settings()
    settings.ensure_dirs()
    if settings.openai_api_key:
        structlog.get_logger("app.main").info("OPENAI_API_KEY is set", llm_enabled=True)
    else:
        structlog.get_logger("app.main").warning(
            "OPENAI_API_KEY is not set; LLM/answers will be disabled. Set it in backend/.env and restart."
        )
    yield
    # Shutdown if needed
    pass


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise GenAI Document Q&A with RAG and Autonomous Agents",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(query_router, prefix=settings.api_prefix)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=getattr(get_settings(), "debug", False),
    )
