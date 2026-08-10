"""
Hybrid Retrieval and Reciprocal Rank Fusion (RRF) Module
Combines dense semantic vector retrieval with BM25 lexical keyword matching.
"""

import math
from typing import List, Dict, Optional, Tuple
from app.mcp.schemas import DocumentChunk


class BM25Retriever:
    """
    Lexical keyword retriever using BM25 scoring algorithm over document chunks.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def search_bm25(
        self,
        query: str,
        corpus_chunks: List[DocumentChunk],
        category: Optional[str] = None,
        top_k: int = 10,
    ) -> List[DocumentChunk]:
        """
        Executes BM25 score calculation over document chunks.
        """
        if not query or not corpus_chunks:
            return []

        # Tokenize query
        query_terms = [t.lower() for t in query.split() if len(t) > 1]
        if not query_terms:
            return []

        # Filter by category if requested
        filtered_chunks = [
            c for c in corpus_chunks
            if not category or c.category.lower() == category.lower()
        ]
        if not filtered_chunks:
            return []

        # Calculate average document length
        doc_lengths = [len(c.content.split()) for c in filtered_chunks]
        avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
        num_docs = len(filtered_chunks)

        # Document frequency per term
        df: Dict[str, int] = {}
        for term in set(query_terms):
            df[term] = sum(1 for c in filtered_chunks if term in c.content.lower())

        scored_chunks: List[Tuple[float, DocumentChunk]] = []

        for idx, chunk in enumerate(filtered_chunks):
            chunk_words = chunk.content.lower().split()
            doc_len = len(chunk_words)
            score = 0.0

            for term in query_terms:
                if df.get(term, 0) == 0:
                    continue
                # Inverse Document Frequency (IDF)
                idf = math.log((num_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                # Term Frequency (TF)
                tf = chunk_words.count(term)
                # BM25 TF weight
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                if denom > 0:
                    score += idf * ((tf * (self.k1 + 1.0)) / denom)

            if score > 0:
                # Normalize BM25 score to [0.0, 1.0] range
                norm_score = round(min(score / (len(query_terms) * 3.0), 1.0), 3)
                chunk_copy = chunk.model_copy(update={"score": max(norm_score, 0.1)})
                scored_chunks.append((score, chunk_copy))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_chunks[:top_k]]


class HybridRetriever:
    """
    Combines dense vector search results and BM25 lexical search results using Reciprocal Rank Fusion (RRF).
    """

    @staticmethod
    def fuse_rrf(
        dense_results: List[DocumentChunk],
        bm25_results: List[DocumentChunk],
        rrf_k: int = 60,
        top_k: int = 10,
    ) -> List[DocumentChunk]:
        """
        Merges dense vector and BM25 search results using RRF score aggregation.
        Formula: RRF_Score(d) = sum( 1 / (rrf_k + rank(d)) )
        """
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # 1. Process Dense Results RRF Ranks
        for rank, chunk in enumerate(dense_results, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        # 2. Process BM25 Results RRF Ranks
        for rank, chunk in enumerate(bm25_results, start=1):
            cid = chunk.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = chunk
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        # Sort combined candidate chunks by aggregated RRF score
        sorted_cids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        fused_chunks: List[DocumentChunk] = []

        for cid in sorted_cids[:top_k]:
            original_chunk = chunk_map[cid]
            rrf_score = round(min(scores[cid] * 30.0, 1.0), 3)  # Rescale to 0.0-1.0 range
            fused_chunks.append(original_chunk.model_copy(update={"score": rrf_score}))

        return fused_chunks
