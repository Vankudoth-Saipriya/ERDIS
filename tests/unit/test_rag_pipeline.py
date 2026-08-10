"""
Comprehensive Unit Tests for Phase 3 Document RAG Pipeline
Tests parsing, chunking, embeddings, Qdrant vector store, BM25, RRF hybrid search, FlashRank reranking,
relevance thresholding, and structured Evidence generation.
"""

import pytest
from app.mcp.schemas import DocumentChunk
from app.schemas.evidence import EvidenceCreate
from app.rag import (
    DocumentParser,
    TextChunker,
    MockEmbeddingProvider,
    get_embedding_provider,
    QdrantVectorStore,
    BM25Retriever,
    HybridRetriever,
    MockReranker,
    RAGPipeline,
    SAMPLE_ENTERPRISE_DOCUMENTS,
)


def test_document_parser_metadata_extraction():
    """Verifies text extraction, metadata parsing, and deterministic document ID generation."""
    content = (
        "# CARRIER CONTRACT 2025\n"
        "Effective Date: 2025-01-01 | Version: 2.1\n\n"
        "SLA breach rate threshold is 5.0%."
    )
    parsed = DocumentParser.parse_text(content, filename="carrier_contract_2025.md")

    assert parsed.document_id == "DOC-CARRIER-CONTRACT-2025"
    assert parsed.category == "contracts"
    assert parsed.effective_date == "2025-01-01"
    assert parsed.doc_version == "2.1"
    assert "SLA breach rate" in parsed.full_text


def test_text_chunker_size_and_overlap():
    """Verifies chunking respects size/overlap limits and preserves metadata on every chunk."""
    content = "\n\n".join([f"Paragraph {i}: " + ("text " * 50) for i in range(10)])
    parsed = DocumentParser.parse_text(content, filename="long_report.md")

    chunker = TextChunker(default_chunk_size=300, default_chunk_overlap=30)
    chunks = chunker.chunk_document(parsed)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.document_id == "DOC-LONG-REPORT"
        assert chunk.source_filename == "long_report.md"
        assert chunk.chunk_id.startswith("DOC-LONG-REPORT-p1#chunk")
        assert chunk.category == "general"


def test_mock_embedding_provider():
    """Verifies deterministic 1536-dimensional L2-normalized float vector generation."""
    provider = MockEmbeddingProvider(dimension=1536)
    vec1 = provider.embed_query("carrier SLA penalty delay")
    vec2 = provider.embed_query("carrier SLA penalty delay")
    vec3 = provider.embed_query("completely different text query")

    assert len(vec1) == 1536
    assert vec1 == vec2  # Deterministic
    assert vec1 != vec3  # Content-sensitive

    # Verify L2 normalization (sum of squares == 1.0)
    norm_sq = sum(x * x for x in vec1)
    assert abs(norm_sq - 1.0) < 1e-4


def test_embedding_provider_factory():
    """Verifies factory returns MockEmbeddingProvider when OPENAI_API_KEY is absent/mock."""
    provider = get_embedding_provider(force_mock=True)
    assert isinstance(provider, MockEmbeddingProvider)


def test_bm25_retriever():
    """Verifies BM25 lexical keyword retrieval and scoring."""
    chunks = [
        DocumentChunk(
            chunk_id="DOC-1-p1#chunk1",
            document_id="DOC-1",
            source_filename="doc1.md",
            category="contracts",
            content="Carrier Logistics Partner X agrees to penalty of $50 per delayed shipment.",
        ),
        DocumentChunk(
            chunk_id="DOC-2-p1#chunk1",
            document_id="DOC-2",
            source_filename="doc2.md",
            category="post_mortems",
            content="Midwest warehouse gross margin erosion was caused by fuel surcharges.",
        ),
    ]

    retriever = BM25Retriever()
    results = retriever.search_bm25(query="carrier penalty delayed shipment", corpus_chunks=chunks)

    assert len(results) >= 1
    assert results[0].document_id == "DOC-1"
    assert results[0].score > 0.0


def test_hybrid_rrf_fusion():
    """Verifies Reciprocal Rank Fusion merges dense and BM25 results deterministically."""
    c1 = DocumentChunk(chunk_id="C1", document_id="D1", source_filename="f1.md", category="cat", content="Content 1")
    c2 = DocumentChunk(chunk_id="C2", document_id="D2", source_filename="f2.md", category="cat", content="Content 2")
    c3 = DocumentChunk(chunk_id="C3", document_id="D3", source_filename="f3.md", category="cat", content="Content 3")

    dense_results = [c1, c2]
    bm25_results = [c2, c3]

    fused = HybridRetriever.fuse_rrf(dense_results=dense_results, bm25_results=bm25_results, top_k=3)

    assert len(fused) == 3
    # C2 was ranked in both lists so it should have the highest RRF score
    assert fused[0].chunk_id == "C2"


def test_mock_reranker():
    """Verifies cross-encoder reranking interface and candidate re-scoring."""
    c1 = DocumentChunk(chunk_id="C1", document_id="D1", source_filename="f1.md", category="cat", content="unrelated topic")
    c2 = DocumentChunk(chunk_id="C2", document_id="D2", source_filename="f2.md", category="cat", content="carrier SLA breach penalty delay")

    reranker = MockReranker()
    reranked = reranker.rerank(query="carrier SLA breach penalty", chunks=[c1, c2], top_k=2)

    assert len(reranked) == 2
    assert reranked[0].chunk_id == "C2"
    assert reranked[0].score > reranked[1].score


def test_rag_pipeline_end_to_end():
    """Verifies end-to-end RAG pipeline: Ingest -> Hybrid Retrieve -> Rerank -> Filter -> Evidence."""
    pipeline = RAGPipeline(embedding_provider=MockEmbeddingProvider(), reranker=MockReranker())
    pipeline.ingest_sample_corpus()

    # Query matching Carrier X SLA terms
    results = pipeline.retrieve_chunks(query="carrier SLA penalty breach 48 hours", top_k=3)
    assert len(results) > 0
    first_chunk = results[0]

    assert first_chunk.document_id == "DOC-CONTRACT-CARRIER-X"
    assert "95.0%" in first_chunk.content or "penalty" in first_chunk.content.lower()

    # Generate Evidence objects
    evidence = pipeline.generate_evidence(query="carrier SLA penalty breach", top_k=2)
    assert len(evidence) > 0
    ev = evidence[0]

    assert isinstance(ev, EvidenceCreate)
    assert ev.source_type == "DOCUMENT"
    assert ev.originating_tool == "mcp-server-documents"
    assert ev.originating_agent == "Document RAG Agent"
    assert ev.content["document_id"] == "DOC-CONTRACT-CARRIER-X"


def test_rag_pipeline_metadata_filtering():
    """Verifies category metadata filtering in RAG pipeline."""
    pipeline = RAGPipeline(embedding_provider=MockEmbeddingProvider(), reranker=MockReranker())
    pipeline.ingest_sample_corpus()

    postmortem_results = pipeline.retrieve_chunks(
        query="midwest hub gross margin fuel",
        category="post_mortems",
        top_k=2,
    )
    assert len(postmortem_results) > 0
    for chunk in postmortem_results:
        assert chunk.category == "post_mortems"


def test_rag_pipeline_empty_retrieval():
    """Verifies non-matching queries return empty results without error."""
    pipeline = RAGPipeline(embedding_provider=MockEmbeddingProvider(), reranker=MockReranker())
    pipeline.ingest_sample_corpus()

    results = pipeline.retrieve_chunks(query="xyz999nonexistentqueryterm", top_k=5, relevance_threshold=0.95)
    assert results == [] or all(c.score >= 0.95 for c in results)


def test_unavailable_qdrant_vector_store_graceful_handling():
    """Verifies vector store gracefully handles unreachable Qdrant client."""
    vs = QdrantVectorStore(client=None)

    assert vs.create_collection_if_not_exists() is False
    assert vs.upsert_chunks([], []) == 0
    assert vs.search_dense([0.1] * 1536) == []
