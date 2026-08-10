"""
End-to-End Document RAG Retrieval Pipeline and Evidence Generator
Coordinates document ingestion, chunking, embedding, vector store search, BM25 keyword matching,
RRF hybrid fusion, FlashRank reranking, relevance score filtering, and structured Evidence generation.
"""

from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.mcp.schemas import DocumentChunk
from app.schemas.evidence import EvidenceCreate
from app.rag.parser import DocumentParser, ParsedDocument
from app.rag.chunker import RecursiveMarkdownChunker
from app.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.rag.vector_store import QdrantVectorStore
from app.rag.hybrid_search import BM25Retriever, HybridRetriever
from app.rag.reranker import BaseReranker, get_reranker
from app.rag.sample_corpus import SAMPLE_ENTERPRISE_DOCUMENTS


class RAGPipeline:
    """
    Production RAG Pipeline and Document Retrieval Service.
    """

    def __init__(
        self,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        reranker: Optional[BaseReranker] = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or QdrantVectorStore()
        self.reranker = reranker or get_reranker()
        self.chunker = RecursiveMarkdownChunker(
            default_chunk_size=settings.CHUNK_SIZE,
            default_chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.bm25_retriever = BM25Retriever()
        self._in_memory_corpus: List[DocumentChunk] = []

    def ingest_document(
        self,
        content: str,
        filename: str,
        category: Optional[str] = None,
        override_doc_id: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """
        Parses, chunks, embeds, and indexes a single document.
        """
        parsed_doc = DocumentParser.parse_text(
            content=content,
            filename=filename,
            category=category,
            override_doc_id=override_doc_id,
        )
        chunks = self.chunker.chunk_document(parsed_doc)

        if not chunks:
            logger.warning("rag_ingest_no_chunks", filename=filename)
            return []

        # Generate embeddings
        chunk_texts = [c.content for c in chunks]
        embeddings = self.embedding_provider.embed_texts(chunk_texts)

        # Index in Qdrant (if available)
        self.vector_store.upsert_chunks(chunks, embeddings)

        # Keep in memory for BM25 and fallback
        for c in chunks:
            if not any(existing.chunk_id == c.chunk_id for existing in self._in_memory_corpus):
                self._in_memory_corpus.append(c)

        logger.info(
            "rag_ingest_success",
            filename=filename,
            doc_id=parsed_doc.document_id,
            chunks_count=len(chunks),
        )
        return chunks

    def ingest_sample_corpus(self) -> int:
        """
        Ingests the deterministic sample enterprise document corpus.
        """
        total_chunks = 0
        for doc_item in SAMPLE_ENTERPRISE_DOCUMENTS:
            chunks = self.ingest_document(
                content=doc_item["content"],
                filename=doc_item["filename"],
                category=doc_item.get("category"),
                override_doc_id=doc_item.get("doc_id"),
            )
            total_chunks += len(chunks)
        return total_chunks

    def retrieve_chunks(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        relevance_threshold: Optional[float] = None,
    ) -> List[DocumentChunk]:
        """
        Executes end-to-end RAG retrieval pipeline:
        Query -> Dense Vector Search + BM25 Search -> Hybrid RRF Fusion -> FlashRank Rerank -> Relevance Threshold Filter
        """
        threshold = relevance_threshold if relevance_threshold is not None else settings.RELEVANCE_THRESHOLD

        # Ensure sample corpus is available if memory is empty
        if not self._in_memory_corpus:
            self.ingest_sample_corpus()

        # Step 1: Dense Semantic Retrieval
        query_vector = self.embedding_provider.embed_query(query)
        dense_candidates = self.vector_store.search_dense(
            query_vector=query_vector,
            category=category,
            top_k=settings.DENSE_TOP_K,
        )

        # Step 2: Lexical BM25 Retrieval
        bm25_candidates = self.bm25_retriever.search_bm25(
            query=query,
            corpus_chunks=self._in_memory_corpus,
            category=category,
            top_k=settings.BM25_TOP_K,
        )

        # Step 3: Hybrid Reciprocal Rank Fusion (RRF)
        fused_candidates = HybridRetriever.fuse_rrf(
            dense_results=dense_candidates,
            bm25_results=bm25_candidates,
            top_k=settings.DENSE_TOP_K + settings.BM25_TOP_K,
        )

        # Fallback if no hybrid candidates found from vector store
        if not fused_candidates and self._in_memory_corpus:
            fused_candidates = self.bm25_retriever.search_bm25(
                query=query,
                corpus_chunks=self._in_memory_corpus,
                category=category,
                top_k=10,
            )

        # Step 4: FlashRank Reranking
        reranked_results = self.reranker.rerank(
            query=query,
            chunks=fused_candidates,
            top_k=settings.RERANK_TOP_K,
        )

        # Step 5: Relevance Threshold Filtering (score >= threshold)
        filtered_chunks: List[DocumentChunk] = []
        for chunk in reranked_results:
            if chunk.score >= threshold or not reranked_results:
                filtered_chunks.append(chunk)

        # Limit to requested top_k
        final_results = (filtered_chunks or reranked_results)[:top_k]

        logger.info(
            "rag_retrieve_completed",
            query=query,
            candidates=len(fused_candidates),
            final_results=len(final_results),
            threshold=threshold,
        )
        return final_results

    def generate_evidence(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[EvidenceCreate]:
        """
        Retrieves top relevant chunks and converts them into structured EvidenceCreate objects.
        """
        chunks = self.retrieve_chunks(query=query, category=category, top_k=top_k)
        evidence_items: List[EvidenceCreate] = []

        for idx, chunk in enumerate(chunks, start=1):
            evidence_id = f"EVID-DOC-{idx:03d}"
            source_ref = f"{chunk.source_filename}#p{chunk.page_number or 1}"

            evidence_items.append(
                EvidenceCreate(
                    evidence_id=evidence_id,
                    source_type="DOCUMENT",
                    source_ref=source_ref,
                    originating_tool="mcp-server-documents",
                    originating_agent="Document RAG Agent",
                    content={
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "source_filename": chunk.source_filename,
                        "category": chunk.category,
                        "page_number": chunk.page_number,
                        "effective_date": chunk.effective_date,
                        "text": chunk.content,
                        "relevance_score": chunk.score,
                    },
                    confidence_score=chunk.score,
                )
            )

        return evidence_items
