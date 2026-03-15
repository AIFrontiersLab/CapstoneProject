"""Application configuration with environment variable support."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to backend project root (parent of app/) so it's always found
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"
# Load .env into os.environ (override=True so .env wins over empty shell OPENAI_API_KEY)
load_dotenv(_ENV_FILE, override=True)


def _read_api_key_from_env_file() -> Optional[str]:
    """Read OPENAI_API_KEY directly from backend/.env if present."""
    if not _ENV_FILE.exists():
        return None
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY=") and not line.startswith("#"):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value and value.lower() not in ("xxx", "your-api-key", "your_key_here"):
                    if not value.lower().startswith(("sk-your-", "sk-placeholder")):
                        return value
                return None
    except Exception:
        pass
    return None


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="Enterprise GenAI Document Q&A", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    max_upload_files: int = Field(default=10, ge=1, le=50, alias="MAX_UPLOAD_FILES")
    max_file_size_mb: int = Field(default=25, ge=1, le=100, alias="MAX_FILE_SIZE_MB")
    rate_limit_requests: int = Field(default=60, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # Storage
    upload_dir: Path = Field(default=Path("data/uploads"), alias="UPLOAD_DIR")
    chroma_persist_dir: Path = Field(
        default=Path("data/chroma"), alias="CHROMA_PERSIST_DIR"
    )
    sqlite_path: Optional[Path] = Field(default=Path("data/metadata.db"), alias="SQLITE_PATH")

    # LLM (OpenAI-compatible)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")

    @field_validator("openai_api_key", mode="after")
    @classmethod
    def normalize_api_key(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v = v.strip()
        # Treat only obvious placeholders as no key (exact or prefix), so real keys are accepted
        lower = v.lower()
        if lower == "xxx" or lower.startswith("sk-your-") or lower.startswith("sk-placeholder"):
            return None
        if lower in ("your-api-key", "your_key_here"):
            return None
        return v

    @model_validator(mode="after")
    def fallback_api_key_from_file(self) -> "Settings":
        """If OPENAI_API_KEY is still missing, read it directly from backend/.env."""
        if self.openai_api_key is None:
            key = _read_api_key_from_env_file()
            if key:
                object.__setattr__(self, "openai_api_key", key)
        return self

    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    # RAG
    chunk_size: int = Field(default=1000, ge=100, le=4000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, ge=0, le=500, alias="CHUNK_OVERLAP")
    top_k_retrieve: int = Field(default=5, ge=1, le=20, alias="TOP_K_RETRIEVE")
    min_relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, alias="MIN_RELEVANCE_SCORE"
    )

    # Fallback: use local embeddings if no API key
    use_local_embeddings: bool = Field(
        default=False, alias="USE_LOCAL_EMBEDDINGS"
    )
    local_embedding_model: str = Field(
        default="all-MiniLM-L6-v2", alias="LOCAL_EMBEDDING_MODEL"
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        """Create required directories if they do not exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        if self.sqlite_path:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
