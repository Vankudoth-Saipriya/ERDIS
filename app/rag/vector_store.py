"""
Qdrant Vector Database Integration Module
Handles Qdrant collection creation, payload indexing, batch upserts, and dense similarity search.
Includes graceful exception handling when Qdrant connection fails.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.core.logging import logger
from app.mcp.schemas import DocumentChunk


class VectorStoreError(Exception):
    """Raised when vector store initialization or operation fails."""
    pass


class QdrantVectorStore:
    """
    Qdrant Vector Database Service Wrapper.
    """

    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._available: Optional[bool] = None

        if client is not None:
            self.client = client
            self._available = True
        else:
            try:
                if settings.QDRANT_URL and "localhost" not in settings.QDRANT_URL:
                    self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=0.1)
                else:
                    self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=0.1)
            except Exception as err:
                logger.warning("qdrant_client_init_failed", error=str(err))
                self.client = None
                self._available = False

    def create_collection_if_not_exists(self) -> bool:
        """
        Ensures target Qdrant collection exists with HNSW index and Cosine distance configuration.
        """
        if self.client is None or self._available is False:
            return False

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE,
                        on_disk=True,
                    ),
                )
                logger.info("qdrant_collection_created", collection_name=self.collection_name)
            self._available = True
            return True
        except Exception as err:
            logger.warning("qdrant_create_collection_error", collection=self.collection_name, error=str(err))
            self._available = False
            return False

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Batch upserts document chunks and vector embeddings into Qdrant payload store.
        """
        if self.client is None or self._available is False or not chunks or not embeddings:
            return 0

        if not self.create_collection_if_not_exists():
            return 0

        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = hash(chunk.chunk_id) & 0x7FFFFFFFFFFFFFFF
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source_filename": chunk.source_filename,
                "category": chunk.category,
                "page_number": chunk.page_number,
                "effective_date": chunk.effective_date,
                "content": chunk.content,
                "untrusted_data": True,
            }
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info("qdrant_upsert_success", count=len(points), collection=self.collection_name)
            return len(points)
        except Exception as err:
            logger.error("qdrant_upsert_failed", collection=self.collection_name, error=str(err))
            self._available = False
            return 0

    def search_dense(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        top_k: int = 10,
    ) -> List[DocumentChunk]:
        """
        Performs dense cosine vector similarity search over Qdrant index.
        """
        if self.client is None or self._available is False or not query_vector or not hasattr(self.client, "search"):
            return []

        filter_condition = None
        if category:
            filter_condition = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="category",
                        match=qmodels.MatchValue(value=category.lower()),
                    )
                ]
            )

        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filter_condition,
                limit=top_k,
            )

            chunks: List[DocumentChunk] = []
            for hit in search_results:
                payload = hit.payload or {}
                chunks.append(
                    DocumentChunk(
                        chunk_id=payload.get("chunk_id", f"DOC-QDRANT-{hit.id}"),
                        document_id=payload.get("document_id", "DOC-UNKNOWN"),
                        source_filename=payload.get("source_filename", "unknown.pdf"),
                        category=payload.get("category", "general"),
                        page_number=payload.get("page_number"),
                        effective_date=payload.get("effective_date"),
                        content=payload.get("content", ""),
                        score=round(float(hit.score), 3),
                    )
                )
            return chunks
        except Exception as err:
            logger.warning("qdrant_search_failed", error=str(err))
            return []
