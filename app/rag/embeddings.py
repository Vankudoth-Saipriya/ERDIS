"""
Embedding Provider Module
Defines an abstract embedding interface and providers for OpenAI (text-embedding-3-small) and Mock/Fake testing.
"""

from abc import ABC, abstractmethod
import hashlib
import math
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class for text embedding models."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of text strings into vector representations."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string into a vector representation."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Embedding Provider using text-embedding-3-small (1536 dimensions).
    Falls back gracefully to MockEmbeddingProvider if API call fails or quota is exhausted.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, dimension: int = 1536):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._fallback_mock = MockEmbeddingProvider(dimension=self.dimension)
        self._disabled = False

        if not self.api_key:
            raise ValueError("OpenAI API Key is required for OpenAIEmbeddingProvider.")

        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._disabled:
            return self._fallback_mock.embed_texts(texts)
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model,
            )
            return [data.embedding for data in response.data]
        except Exception as err:
            logger.warning("openai_embedding_failure_fallback_to_mock", model=self.model, error=str(err))
            self._disabled = True
            return self._fallback_mock.embed_texts(texts)

    def embed_query(self, query: str) -> List[float]:
        if self._disabled:
            return self._fallback_mock.embed_query(query)
        try:
            response = self.client.embeddings.create(
                input=[query],
                model=self.model,
            )
            return response.data[0].embedding
        except Exception as err:
            logger.warning("openai_embedding_failure_fallback_to_mock", model=self.model, error=str(err))
            self._disabled = True
            return self._fallback_mock.embed_query(query)


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Mock/Fake Embedding Provider generating deterministic 1536-dimensional vectors for testing and offline execution.
    Calculates L2-normalized float vectors from SHA256 hashes of input text.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        # Generate deterministic vector from SHA-256 hash of text
        vec = []
        base_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()

        for i in range(self.dimension):
            # Deterministic value in [-1.0, 1.0]
            val = ((int(base_hash[(i % len(base_hash))], 16) + i) % 200 - 100) / 100.0
            vec.append(val)

        # L2 Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]

        return vec


def get_embedding_provider(
    force_mock: bool = False,
    api_key: Optional[str] = None,
) -> BaseEmbeddingProvider:
    """
    Factory function for obtaining an embedding provider.
    Defaults to MockEmbeddingProvider if running in pytest, or if OPENAI_API_KEY is dummy, missing, or force_mock is True.
    """
    import sys
    key = api_key or settings.OPENAI_API_KEY
    if (
        "pytest" in sys.modules
        or force_mock
        or not key
        or key.startswith("your_")
        or key == "your_openai_api_key_here"
        or "sk-dummy" in key
    ):
        return MockEmbeddingProvider()

    try:
        return OpenAIEmbeddingProvider(api_key=key)
    except Exception as err:
        logger.warning("fallback_to_mock_embedding_provider", reason=str(err))
        return MockEmbeddingProvider()
