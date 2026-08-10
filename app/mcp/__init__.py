"""
Model Context Protocol (MCP) Server Package
Exposes SQL and Document MCP Servers, Schemas, and Validation Utilities.
"""

from app.mcp.schemas import (
    ExecuteSQLRequest,
    SQLQueryResult,
    TableSchemaRequest,
    TableSchemaResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentFetchRequest,
    DocumentFetchResult,
    DocumentChunk,
)
from app.mcp.sql_validator import (
    validate_and_enforce_sql,
    SQLSecurityError,
    ALLOWLISTED_TABLES,
)
from app.mcp.sql_server import SQLMCPServer, TABLE_SCHEMAS_DDL
from app.mcp.document_server import DocumentMCPServer

__all__ = [
    "ExecuteSQLRequest",
    "SQLQueryResult",
    "TableSchemaRequest",
    "TableSchemaResponse",
    "DocumentSearchRequest",
    "DocumentSearchResult",
    "DocumentFetchRequest",
    "DocumentFetchResult",
    "DocumentChunk",
    "validate_and_enforce_sql",
    "SQLSecurityError",
    "ALLOWLISTED_TABLES",
    "SQLMCPServer",
    "TABLE_SCHEMAS_DDL",
    "DocumentMCPServer",
]
