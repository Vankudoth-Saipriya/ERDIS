"""
Model Context Protocol (MCP) Pydantic Tool Contracts
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


# --- SQL MCP Server Schemas ---

class ExecuteSQLRequest(BaseModel):
    sql_query: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Read-only SQL query to execute."
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Task ID for audit logging and evidence tracking."
    )


class SQLQueryResult(BaseModel):
    success: bool
    query_id: str = Field(default_factory=lambda: f"SQL-{uuid4().hex[:8]}")
    sql_query: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class TableSchemaRequest(BaseModel):
    table_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional table name to retrieve DDL for. If omitted, returns all allowlisted tables."
    )


class TableSchemaResponse(BaseModel):
    success: bool
    schemas: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    allowlisted_tables: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# --- Document MCP Server Schemas ---

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_filename: str
    category: str
    page_number: Optional[int] = None
    effective_date: Optional[str] = None
    content: str
    score: float = 1.0


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    category: Optional[str] = Field(default=None, max_length=100, description="Optional category filter (e.g., 'contracts', 'post_mortems')")
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    success: bool
    search_id: str = Field(default_factory=lambda: f"DOC-{uuid4().hex[:8]}")
    documents: List[DocumentChunk] = Field(default_factory=list)
    total_results: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class DocumentFetchRequest(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=100, description="Unique document ID to retrieve.")


class DocumentFetchResult(BaseModel):
    success: bool
    document_id: str
    source_filename: Optional[str] = None
    full_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
