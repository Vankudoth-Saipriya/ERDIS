"""
RAG Pipeline Package
Exposes Document Parser, Chunker, Embedding Providers, Vector Store, Hybrid Search, Rerankers, and RAG Pipeline.
"""

from app.rag.parser import DocumentParser, ParsedDocument, DocumentParsingError
from app.rag.chunker import RecursiveMarkdownChunker, TextChunker
from app.rag.embeddings import BaseEmbeddingProvider, OpenAIEmbeddingProvider, MockEmbeddingProvider, get_embedding_provider
from app.rag.vector_store import QdrantVectorStore, VectorStoreError
from app.rag.hybrid_search import BM25Retriever, HybridRetriever
from app.rag.reranker import BaseReranker, FlashRankReranker, MockReranker, get_reranker
from app.rag.retrieval import RAGPipeline
from app.rag.sample_corpus import SAMPLE_ENTERPRISE_DOCUMENTS

__all__ = [
    "DocumentParser",
    "ParsedDocument",
    "DocumentParsingError",
    "RecursiveMarkdownChunker",
    "TextChunker",
    "BaseEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
    "QdrantVectorStore",
    "VectorStoreError",
    "BM25Retriever",
    "HybridRetriever",
    "BaseReranker",
    "FlashRankReranker",
    "MockReranker",
    "get_reranker",
    "RAGPipeline",
    "SAMPLE_ENTERPRISE_DOCUMENTS",
]
