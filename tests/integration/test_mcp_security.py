"""
Integration Tests for MCP Server Security Boundaries and Tool Contracts
Verifies end-to-end tool execution schemas, security isolation, and structured error handling.
"""

import pytest
from app.mcp import (
    SQLMCPServer,
    DocumentMCPServer,
    ExecuteSQLRequest,
    TableSchemaRequest,
    DocumentSearchRequest,
    DocumentFetchRequest,
    SQLQueryResult,
    TableSchemaResponse,
    DocumentSearchResult,
    DocumentFetchResult,
)


@pytest.mark.asyncio
async def test_sql_mcp_boundary_isolation():
    """
    Verifies that SQL MCP Server exposes only structured Pydantic results
    and never leaks raw DB connections or credentials.
    """
    server = SQLMCPServer()

    # 1. Test DDL Schema response contract
    schema_req = TableSchemaRequest()
    schema_res = server.get_table_schemas(schema_req)
    assert isinstance(schema_res, TableSchemaResponse)
    assert schema_res.success is True
    assert "orders" in schema_res.schemas

    # 2. Test SQL query execution response contract
    exec_req = ExecuteSQLRequest(sql_query="SELECT * FROM orders", task_id="INT-TEST-01")
    exec_res = await server.execute_read_only_sql(exec_req)
    assert isinstance(exec_res, SQLQueryResult)
    # Ensure no passwords or DB URIs exist in output
    res_json = exec_res.model_dump_json()
    assert "postgresql://" not in res_json
    assert "erdis_password" not in res_json


@pytest.mark.asyncio
async def test_document_mcp_boundary_isolation():
    """
    Verifies that Document MCP Server exposes only controlled search & fetch outputs
    and preserves citation metadata without raw filesystem exposure.
    """
    server = DocumentMCPServer()

    # 1. Search response contract
    search_req = DocumentSearchRequest(query="SLA breach penalty", top_k=2)
    search_res = await server.search_documents(search_req)
    assert isinstance(search_res, DocumentSearchResult)
    assert search_res.success is True

    # 2. Fetch response contract
    fetch_req = DocumentFetchRequest(document_id="DOC-CONTRACT-CARRIER-X")
    fetch_res = await server.get_document_by_id(fetch_req)
    assert isinstance(fetch_res, DocumentFetchResult)
    assert fetch_res.success is True
    assert fetch_res.document_id == "DOC-CONTRACT-CARRIER-X"
