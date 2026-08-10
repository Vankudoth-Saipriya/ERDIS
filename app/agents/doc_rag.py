"""
Document RAG Agent Implementation.
Formulates search queries and executes them strictly through the Document MCP Server boundary.
Enforces untrusted data framing (<UNTRUSTED_DOCUMENT>...</UNTRUSTED_DOCUMENT>) on all retrieved passages.
"""

from typing import Optional, List
from app.services.llm_provider import BaseLLMProvider, get_llm_provider
from app.schemas.agents import DocumentAnalysisOutput
from app.agents.prompts import DOCUMENT_RAG_SYSTEM_PROMPT
from app.mcp.document_server import DocumentMCPServer
from app.mcp.schemas import DocumentSearchRequest


class DocumentRAGAgent:
    """
    Document RAG Agent restricted strictly to the Document MCP Server boundary.
    """

    def __init__(
        self,
        doc_server: Optional[DocumentMCPServer] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.doc_server = doc_server or DocumentMCPServer()
        self.llm_provider = llm_provider or get_llm_provider()

    async def search(self, question: str, category: Optional[str] = None, top_k: int = 3) -> DocumentAnalysisOutput:
        """
        Executes document search via Document MCP Server, frames text in untrusted delimiters, and returns DocumentAnalysisOutput.
        """
        # Formulate search request
        mcp_res = await self.doc_server.search_documents(
            DocumentSearchRequest(query=question, category=category, top_k=top_k)
        )

        if not mcp_res.success or not mcp_res.documents:
            return DocumentAnalysisOutput(
                search_query=question,
                retrieved_chunks_summary="No relevant document chunks found.",
                citations=[],
                insufficient_evidence=True,
            )

        # Wrap retrieved passages inside UNTRUSTED_DOCUMENT security framing
        framed_chunks = []
        citations = []
        for doc in mcp_res.documents:
            framed_chunks.append(
                f"<UNTRUSTED_DOCUMENT>\n"
                f"Document ID: {doc.document_id}\n"
                f"Chunk ID: {doc.chunk_id}\n"
                f"Source: {doc.source_filename} (Page {doc.page_number})\n"
                f"Content: {doc.content}\n"
                f"</UNTRUSTED_DOCUMENT>"
            )
            citations.append(f"{doc.source_filename}#p{doc.page_number}")

        prompt = (
            f"Analyze the following retrieved document passages for the query:\n"
            f"Query: {question}\n\n"
            + "\n\n".join(framed_chunks)
        )

        output = self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=DocumentAnalysisOutput,
            system_prompt=DOCUMENT_RAG_SYSTEM_PROMPT,
        )

        return DocumentAnalysisOutput(
            search_query=question,
            retrieved_chunks_summary=output.retrieved_chunks_summary or f"Retrieved {len(mcp_res.documents)} chunks.",
            citations=citations,
            insufficient_evidence=False,
        )
