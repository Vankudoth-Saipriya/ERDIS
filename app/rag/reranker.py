"""
FlashRank Cross-Encoder Reranking Module
Reranks candidate document chunks using lightweight ONNX model (ms-marco-TinyBERT-L-2-v2).
Includes a fail-safe fallback mechanism if reranker initialization or inference fails.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.mcp.schemas import DocumentChunk


class BaseReranker(ABC):
    """Abstract Base Class for document cross-encoder rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: int = 5,
    ) -> List[DocumentChunk]:
        """Reranks candidate chunks with respect to query."""
        pass


class FlashRankReranker(BaseReranker):
    """
    FlashRank Cross-Encoder Reranker using ONNX model ms-marco-TinyBERT-L-2-v2 (~40MB RAM footprint).
    """

    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.model_name = model_name
        self._ranker = None
        try:
            from flashrank import Ranker
            self._ranker = Ranker(model_name=self.model_name)
        except Exception as err:
            logger.warning("flashrank_init_warning", model=self.model_name, error=str(err))
            self._ranker = None

    def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: int = 5,
    ) -> List[DocumentChunk]:
        if not chunks or not query:
            return []

        if self._ranker is None:
            logger.warning("flashrank_unavailable_fallback_to_candidate_order")
            return chunks[:top_k]

        try:
            from flashrank import RerankRequest

            # Construct passaged dicts for FlashRank
            passages = [
                {"id": c.chunk_id, "text": c.content, "meta": c.model_dump()}
                for c in chunks
            ]
            rerank_req = RerankRequest(query=query, passages=passages)
            results = self._ranker.rerank(rerank_req)

            reranked_chunks: List[DocumentChunk] = []
            chunk_map = {c.chunk_id: c for c in chunks}

            for res in results[:top_k]:
                cid = res.get("id")
                score = round(float(res.get("score", 0.5)), 3)
                if cid in chunk_map:
                    updated = chunk_map[cid].model_copy(update={"score": score})
                    reranked_chunks.append(updated)

            return reranked_chunks
        except Exception as err:
            logger.error("flashrank_rerank_failed", error=str(err))
            # Fail-safe: Return original candidates sorted by candidate score
            return chunks[:top_k]


class MockReranker(BaseReranker):
    """
    Mock Reranker for unit testing without ONNX model loading overhead.
    """

    def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: int = 5,
    ) -> List[DocumentChunk]:
        if not chunks:
            return []

        # Simple term density re-scoring
        query_terms = set(query.lower().split())
        scored = []
        for c in chunks:
            text_terms = set(c.content.lower().split())
            overlap = len(query_terms.intersection(text_terms))
            score = round(min(0.5 + (overlap * 0.1), 0.99), 2)
            scored.append(c.model_copy(update={"score": score}))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]


_GLOBAL_RERANKER_CACHE: Optional[BaseReranker] = None


def get_reranker(force_mock: bool = False) -> BaseReranker:
    """
    Factory function for obtaining a reranker instance with singleton caching.
    """
    global _GLOBAL_RERANKER_CACHE

    if force_mock:
        return MockReranker()

    if _GLOBAL_RERANKER_CACHE is None:
        try:
            _GLOBAL_RERANKER_CACHE = FlashRankReranker()
        except Exception as err:
            logger.warning("flashrank_cache_fallback_to_mock", error=str(err))
            _GLOBAL_RERANKER_CACHE = MockReranker()

    return _GLOBAL_RERANKER_CACHE
