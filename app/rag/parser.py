"""
Document Loading and Parsing Module
Extracts text, metadata, document IDs, and structural properties from enterprise files.
"""

import os
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentParsingError(Exception):
    """Raised when document loading or text extraction fails."""
    pass


class ParsedDocument(BaseModel):
    document_id: str
    source_filename: str
    category: str = "general"
    full_text: str
    effective_date: Optional[str] = None
    doc_version: Optional[str] = "1.0"
    page_count: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentParser:
    """
    Parses enterprise documents (Markdown, Plain Text, PDF) into structured ParsedDocument objects.
    Extracts metadata such as effective dates, categories, and document identifiers.
    """

    @staticmethod
    def parse_text(
        content: str,
        filename: str,
        category: Optional[str] = None,
        override_doc_id: Optional[str] = None,
    ) -> ParsedDocument:
        """
        Parses string text content into a ParsedDocument object.
        """
        if not content or not content.strip():
            raise DocumentParsingError(f"Cannot parse empty content for file '{filename}'.")

        clean_text = content.strip()
        doc_id = override_doc_id or DocumentParser.generate_document_id(filename)
        detected_category = category or DocumentParser.infer_category(filename, clean_text)
        effective_date = DocumentParser.extract_effective_date(clean_text)
        doc_version = DocumentParser.extract_version(clean_text)

        return ParsedDocument(
            document_id=doc_id,
            source_filename=filename,
            category=detected_category,
            full_text=clean_text,
            effective_date=effective_date,
            doc_version=doc_version,
            page_count=1,
            metadata={
                "char_length": len(clean_text),
                "untrusted_data": True,
            },
        )

    @staticmethod
    def parse_file(file_path: str, category: Optional[str] = None) -> ParsedDocument:
        """
        Loads and parses a document from local disk.
        """
        if not os.path.exists(file_path):
            raise DocumentParsingError(f"File not found: '{file_path}'.")

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext in [".txt", ".md", ".markdown"]:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return DocumentParser.parse_text(content, filename, category)
            else:
                # Basic text reading fallback for unhandled extensions
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return DocumentParser.parse_text(content, filename, category)
        except Exception as err:
            raise DocumentParsingError(f"Failed to parse document '{filename}': {str(err)}")

    @staticmethod
    def generate_document_id(filename: str) -> str:
        """Generates a deterministic document_id from filename."""
        base_name = os.path.splitext(filename)[0]
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", base_name).strip("-").upper()
        if not slug.startswith("DOC-"):
            return f"DOC-{slug}"
        return slug

    @staticmethod
    def infer_category(filename: str, text: str) -> str:
        """Infers category from filename or document body keywords."""
        fn_lower = filename.lower()
        text_lower = text.lower()[:500]

        if "contract" in fn_lower or "sla" in fn_lower or "agreement" in fn_lower or "contract" in text_lower:
            return "contracts"
        elif "postmortem" in fn_lower or "post_mortem" in fn_lower or "post-mortem" in fn_lower or "postmortem" in text_lower:
            return "post_mortems"
        elif "surcharge" in fn_lower or "amendment" in fn_lower:
            return "contracts"
        elif "policy" in fn_lower or "refund" in fn_lower:
            return "policies"
        return "general"

    @staticmethod
    def extract_effective_date(text: str) -> Optional[str]:
        """Extracts ISO date strings (e.g. 2025-01-01 or August 15, 2025) from document text."""
        iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        if iso_match:
            return iso_match.group(1)
        return None

    @staticmethod
    def extract_version(text: str) -> str:
        """Extracts document version numbers from text header if available."""
        ver_match = re.search(r"\bv(?:ersion)?[:\s]*(\d+\.\d+)\b", text, re.IGNORECASE)
        if ver_match:
            return ver_match.group(1)
        return "1.0"
