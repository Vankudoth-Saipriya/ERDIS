"""
Deterministic Routing Engine for ERDIS LangGraph Execution.
Analyzes normalized user questions and plans to classify required evidence paths (SQL, Document, Both, Clarification).
"""

from typing import Dict, Any, Literal, Optional

SQL_KEYWORDS = {
    "revenue", "margin", "sales", "order", "orders", "cost", "refund", "refunds",
    "amount", "count", "sum", "average", "total", "database", "table", "sql",
    "profit", "shipping_cost", "volume", "discounts",
}

DOC_KEYWORDS = {
    "policy", "contract", "agreement", "sla", "postmortem", "document", "docs",
    "pdf", "amendment", "terms", "clause", "notice", "guideline", "rule",
    "exception", "clause", "tier", "delay",
}


def determine_route(
    question: str,
    plan: Optional[Dict[str, Any]] = None,
) -> Literal["sql_only", "document_only", "both", "clarification"]:
    """
    Deterministically routes user query based on keyword analysis and plan structure.
    Does NOT invoke external LLMs.
    """
    if not question or len(question.strip()) < 3:
        return "clarification"

    q_lower = question.lower()

    # Check for gibberish or explicit non-queries
    if q_lower in {"hi", "hello", "test", "abc", "asdf"}:
        return "clarification"

    has_sql = any(kw in q_lower for kw in SQL_KEYWORDS)
    has_doc = any(kw in q_lower for kw in DOC_KEYWORDS)

    if has_sql and has_doc:
        return "both"
    elif has_sql:
        return "sql_only"
    elif has_doc:
        return "document_only"
    else:
        # Default fallback for meaningful questions: query both sources
        return "both"
