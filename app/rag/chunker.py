"""
Document Chunking Module
Splits parsed documents into context-preserving text chunks with deterministic IDs and metadata attachments.
"""

from typing import List, Optional
from app.mcp.schemas import DocumentChunk
from app.rag.parser import ParsedDocument


class TextChunker:
    """
    Configurable document chunker.
    Splits text by paragraphs or sentence boundaries while preserving document metadata on every chunk.
    """

    def __init__(self, default_chunk_size: int = 500, default_chunk_overlap: int = 50):
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap

    def chunk_document(
        self,
        doc: ParsedDocument,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """
        Splits a ParsedDocument into a list of metadata-enriched DocumentChunk objects.
        """
        size = chunk_size or self.default_chunk_size
        overlap = chunk_overlap or self.default_chunk_overlap

        # Split text into paragraphs
        paragraphs = [p.strip() for p in doc.full_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [doc.full_text.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk_paragraphs: List[str] = []
        current_char_count = 0
        seq = 1

        for para in paragraphs:
            para_len = len(para)
            if current_char_count + para_len > size and current_chunk_paragraphs:
                # Construct chunk content
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunk_id = f"{doc.document_id}-p1#chunk{seq}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        source_filename=doc.source_filename,
                        category=doc.category,
                        page_number=1,
                        effective_date=doc.effective_date,
                        content=chunk_text,
                        score=1.0,
                    )
                )
                seq += 1

                # Keep overlap paragraphs if available
                if overlap > 0 and len(current_chunk_paragraphs) > 1:
                    current_chunk_paragraphs = current_chunk_paragraphs[-1:]
                    current_char_count = len(current_chunk_paragraphs[0])
                else:
                    current_chunk_paragraphs = []
                    current_char_count = 0

            current_chunk_paragraphs.append(para)
            current_char_count += para_len

        # Final remaining chunk
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunk_id = f"{doc.document_id}-p1#chunk{seq}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    source_filename=doc.source_filename,
                    category=doc.category,
                    page_number=1,
                    effective_date=doc.effective_date,
                    content=chunk_text,
                    score=1.0,
                )
            )

        return chunks


RecursiveMarkdownChunker = TextChunker
