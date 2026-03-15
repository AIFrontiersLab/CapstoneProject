"""Embedding service abstraction: OpenAI or local sentence-transformers."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts. Returns list of vectors."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI (or compatible API) embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = None
        self.model = settings.embedding_model
        self.api_key = settings.openai_api_key
        self.api_base = settings.openai_api_base
        if self.api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.api_key}
                if self.api_base:
                    kwargs["base_url"] = self.api_base
                self.client = OpenAI(**kwargs)
            except Exception as e:
                logger.warning("openai_client_init_failed", error=str(e))

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.client or not texts:
            return []
        try:
            r = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in r.data]
        except Exception as e:
            logger.exception("embed_documents_error", error=str(e))
            raise

    def embed_query(self, text: str) -> List[float]:
        if not self.client:
            return []
        r = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return r.data[0].embedding


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.local_embedding_model
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        return model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        return model.encode([text], convert_to_numpy=True)[0].tolist()


class EmbeddingService:
    """High-level embedding service with provider abstraction."""

    def __init__(self) -> None:
        settings = get_settings()
        if settings.use_local_embeddings or not settings.openai_api_key:
            self._provider: EmbeddingProvider = LocalEmbeddingProvider()
            logger.info("using_local_embeddings", model=settings.local_embedding_model)
        else:
            self._provider = OpenAIEmbeddingProvider()
            if not getattr(self._provider, "client", None):
                self._provider = LocalEmbeddingProvider()
                logger.info("fallback_to_local_embeddings")
        self._provider = self._provider

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._provider.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._provider.embed_query(text)


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
