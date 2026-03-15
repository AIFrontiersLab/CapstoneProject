"""Shared LLM factory using LangChain core (BaseChatModel).

Agents and RAG use this to get a chat model. Implementation is OpenAI-compatible
(langchain_openai) but callers depend only on langchain_core interfaces
(messages, invoke). Other providers (Anthropic, etc.) can be added via config later.
"""

from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_llm: Optional[BaseChatModel] = None


def get_llm() -> Optional[BaseChatModel]:
    """Return a LangChain BaseChatModel (OpenAI-compatible by default). Lazy init."""
    global _llm
    if _llm is not None:
        return _llm
    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("llm_skipped", reason="OPENAI_API_KEY not set")
        return None
    try:
        from langchain_openai import ChatOpenAI

        _llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            temperature=0,
        )
        return _llm
    except Exception as e:
        logger.warning("llm_init_failed", error=str(e))
        return None
