"""
ERDIS Application Settings & Configuration Management
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Settings
    APP_NAME: str = "ERDIS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database Settings
    POSTGRES_USER: str = "erdis_user"
    POSTGRES_PASSWORD: str = "erdis_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "erdis_system_db"

    # Read-Only Database Role (for SQL Agent)
    READONLY_DB_USER: str = "erdis_readonly"
    READONLY_DB_PASSWORD: str = "erdis_readonly_password"

    # Qdrant Vector DB Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "erdis_documents"

    # OpenAI API Key
    OPENAI_API_KEY: Optional[str] = None

    # RAG Pipeline Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    DENSE_TOP_K: int = 10
    BM25_TOP_K: int = 10
    RERANK_TOP_K: int = 5
    RELEVANCE_THRESHOLD: float = 0.65

    # Circuit Breakers & Resource Safety
    MAX_CRITIC_LOOPS: int = 2
    MAX_TOOL_CALLS_PER_RUN: int = 10
    MAX_TOKEN_BUDGET_PER_RUN: int = 60000
    EXECUTION_TIMEOUT_SECONDS: float = 45.0
    HIGH_FINANCIAL_IMPACT_THRESHOLD_USD: float = 100000.0

    @property
    def database_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
