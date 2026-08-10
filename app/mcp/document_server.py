"""
Document Model Context Protocol (MCP) Server Implementation

Provides controlled document retrieval tools over enterprise contracts, post-mortems, and SLA agreements.
Integrates with the RAG Pipeline (Qdrant dense search, BM25 lexical search, RRF hybrid fusion, FlashRank reranking).
Treats all retrieved text as UNTRUSTED DATA, preserves citation metadata, enforces input validation,
and handles vector storage (Qdrant) connection failures gracefully.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger
from app.mcp.schemas import (
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentFetchRequest,
    DocumentFetchResult,
    DocumentChunk,
)


class DocumentMCPServer:
    """
    Model Context Protocol (MCP) Server for Document Search and Retrieval.
    Provides isolated, read-only search tools powered by the RAG Pipeline.
    Enforces security boundaries (untrusted data framing), citation preservation, timeout limits, and audit logging.
    """

    def __init__(
        self,
        rag_pipeline: Optional[Any] = None,
        qdrant_client: Optional[Any] = None,
    ):
        """
        Initializes the Document MCP Server.
        Optionally accepts a custom RAGPipeline instance.
        """
        if rag_pipeline is not None:
            self.rag_pipeline = rag_pipeline
        else:
            from app.rag.retrieval import RAGPipeline
            from app.rag.vector_store import QdrantVectorStore
            self.rag_pipeline = RAGPipeline(
                vector_store=QdrantVectorStore(client=qdrant_client)
            )

    async def search_documents(
        self,
        request: DocumentSearchRequest,
        timeout_seconds: float = 3.0,
    ) -> DocumentSearchResult:
        """
        Searches document chunks matching user query and optional category filter using the RAG Pipeline.
        Enforces timeout limits, handles Qdrant unavailability gracefully, and preserves citation metadata.
        """
        start_time = time.perf_counter()
        query_str = request.query.strip()
        category_filter = request.category.lower() if request.category else None
        top_k = request.top_k

        # Input Validation
        if not query_str or len(query_str) < 2:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning("doc_mcp_malformed_query", query=request.query)
            return DocumentSearchResult(
                success=False,
                error="Search query must be at least 2 characters in length.",
                execution_time_ms=duration_ms,
            )

        try:
            results = await asyncio.wait_for(
                self._execute_search_async(query_str, category_filter, top_k),
                timeout=timeout_seconds,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "doc_mcp_search_success",
                query=query_str,
                category=category_filter,
                top_k=top_k,
                results_count=len(results),
                duration_ms=duration_ms,
            )

            return DocumentSearchResult(
                success=True,
                documents=results,
                total_results=len(results),
                execution_time_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "doc_mcp_search_timeout",
                query=query_str,
                timeout_seconds=timeout_seconds,
                duration_ms=duration_ms,
            )
            return DocumentSearchResult(
                success=False,
                error=f"Document search timed out after {timeout_seconds} seconds.",
                execution_time_ms=duration_ms,
            )
        except Exception as err:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("doc_mcp_search_error", query=query_str, error=str(err))
            return DocumentSearchResult(
                success=False,
                error=f"Document search error: {str(err)}",
                execution_time_ms=duration_ms,
            )

    async def get_document_by_id(
        self,
        request: DocumentFetchRequest,
        timeout_seconds: float = 3.0,
    ) -> DocumentFetchResult:
        """
        Retrieves full document text and metadata by document_id.
        """
        start_time = time.perf_counter()
        doc_id = request.document_id.strip()

        if not doc_id:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return DocumentFetchResult(
                success=False,
                document_id=doc_id,
                error="document_id parameter cannot be empty.",
            )

        # Search in RAG pipeline corpus (ensuring sample corpus is ingested if needed)
        if not self.rag_pipeline._in_memory_corpus:
            self.rag_pipeline.ingest_sample_corpus()

        matched_doc = None
        for chunk in self.rag_pipeline._in_memory_corpus:
            if chunk.document_id.lower() == doc_id.lower():
                matched_doc = chunk
                break

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if matched_doc:
            logger.info("doc_mcp_fetch_success", document_id=doc_id, duration_ms=duration_ms)
            return DocumentFetchResult(
                success=True,
                document_id=matched_doc.document_id,
                source_filename=matched_doc.source_filename,
                full_text=matched_doc.content,
                metadata={
                    "category": matched_doc.category,
                    "effective_date": matched_doc.effective_date,
                    "untrusted_data": True,
                },
            )
        else:
            logger.warning("doc_mcp_fetch_not_found", document_id=doc_id, duration_ms=duration_ms)
            return DocumentFetchResult(
                success=False,
                document_id=doc_id,
                error=f"Document with ID '{doc_id}' not found.",
            )

    async def _execute_search_async(
        self,
        query: str,
        category: Optional[str],
        top_k: int,
    ) -> List[DocumentChunk]:
        """
        Executes document search via RAG Pipeline in an async executor thread.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.rag_pipeline.retrieve_chunks, query, category, top_k)
