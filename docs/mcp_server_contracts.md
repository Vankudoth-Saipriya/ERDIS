# Model Context Protocol (MCP) Server Contracts & Security Specification

This document details the interface contracts, execution flows, and security boundaries for the two standalone MCP servers implemented in Phase 2 of ERDIS:

1. `mcp-server-sql` (Read-only Database Operations with AST Security)
2. `mcp-server-documents` (Controlled Contract & Post-Mortem Document Retrieval)

---

## 1. SQL MCP Server (`mcp-server-sql`)

### 1.1 Architecture & Pipeline Flow
```
Client Request (ExecuteSQLRequest)
        │
        ▼
1. AST Validation (SQLGlot) ──► Rejects INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/GRANT/REVOKE/Multi-Stmt
        │
        ▼
2. Table Authorization ──► Checks accessed physical tables against ALLOWLISTED_TABLES
        │
        ▼
3. Policy Enforcement ──► Rejects Cartesian JOINs (without ON/USING), enforces max 100 row LIMIT
        │
        ▼
4. Database Execution ──► Executes via read-only DB role (`erdis_readonly`) with 5s timeout
        │
        ▼
Structured Result (SQLQueryResult) ──► Audit logging & password masking (no credentials exposed)
```

### 1.2 Tool Surface

#### Tool 1: `get_table_schemas`
- **Description**: Returns DDL summaries and metadata for authorized business tables.
- **Input Schema**: `TableSchemaRequest`
  - `table_name`: Optional `str` (e.g., `"orders"`, `"carriers"`). Omit to retrieve all table schemas.
- **Output Schema**: `TableSchemaResponse`
  - `success`: `bool`
  - `schemas`: `Dict[str, Dict[str, Any]]`
  - `allowlisted_tables`: `List[str]` (`["carriers", "inventory", "orders", "returns", "shipments", "suppliers"]`)
  - `error`: `Optional[str]`

#### Tool 2: `execute_read_only_sql`
- **Description**: Validates and executes a read-only SQL query against PostgreSQL.
- **Input Schema**: `ExecuteSQLRequest`
  - `sql_query`: `str` (5 to 4000 chars)
  - `task_id`: `Optional[str]` (Audit tracking ID)
- **Output Schema**: `SQLQueryResult`
  - `success`: `bool`
  - `query_id`: `str` (`"SQL-xxxxxxxx"`)
  - `sql_query`: `str` (Sanitized and limit-enforced query)
  - `columns`: `List[str]`
  - `rows`: `List[Dict[str, Any]]`
  - `row_count`: `int`
  - `execution_time_ms`: `float`
  - `error`: `Optional[str]`

### 1.3 Security Controls & Boundary Safeguards
- **SELECT-Only Enforcement**: Rejects all data mutation and schema DDL statements.
- **AST Parsing**: SQLGlot parses the complete AST prior to execution. Does not rely on naive regex keyword matching.
- **CTE Alias Isolation**: Recognizes temporary CTE table aliases without blocking valid `WITH` queries.
- **Cartesian Join Prevention**: Rejects explicit `CROSS JOIN`, implicit comma joins (`FROM orders, shipments`), or `JOIN` without `ON`/`USING` clauses.
- **Row Limit Enforcement**: Automatically appends or caps result size to **100 rows max**.
- **Statement Timeout**: Execution bounded by a strict **5.0 second timeout**.
- **Credential Masking**: Database connection strings, passwords, and host IP addresses are sanitized before emitting errors or logs.

---

## 2. Document MCP Server (`mcp-server-documents`)

### 2.1 Architecture & Pipeline Flow
```
Client Request (DocumentSearchRequest / DocumentFetchRequest)
        │
        ▼
1. Input Validation ──► Validates query length (≥2 chars), top_k bounds (1..20), category string
        │
        ▼
2. Controlled Retrieval ──► Searches Qdrant collection or built-in document corpus fallback
        │
        ▼
3. Untrusted Data Framing ──► Treats retrieved document chunks as UNTRUSTED DATA
        │
        ▼
4. Citation Preservation ──► Retains source metadata (`chunk_id`, `document_id`, `page_number`, etc.)
        │
        ▼
Structured Result (DocumentSearchResult / DocumentFetchResult) ──► Audit logging & safe response payload
```

### 2.2 Tool Surface

#### Tool 1: `search_documents`
- **Description**: Performs targeted keyword/vector retrieval over contracts and post-mortems.
- **Input Schema**: `DocumentSearchRequest`
  - `query`: `str` (2 to 1000 chars)
  - `category`: `Optional[str]` (e.g. `"contracts"`, `"post_mortems"`)
  - `top_k`: `int` (default `5`, min `1`, max `20`)
- **Output Schema**: `DocumentSearchResult`
  - `success`: `bool`
  - `search_id`: `str` (`"DOC-xxxxxxxx"`)
  - `documents`: `List[DocumentChunk]`
  - `total_results`: `int`
  - `execution_time_ms`: `float`
  - `error`: `Optional[str]`

#### Tool 2: `get_document_by_id`
- **Description**: Fetches full document text and metadata by unique document identifier.
- **Input Schema**: `DocumentFetchRequest`
  - `document_id`: `str`
- **Output Schema**: `DocumentFetchResult`
  - `success`: `bool`
  - `document_id`: `str`
  - `source_filename`: `Optional[str]`
  - `full_text`: `Optional[str]`
  - `metadata`: `Dict[str, Any]` (flags `untrusted_data: true`)
  - `error`: `Optional[str]`

### 2.3 Security Controls & Boundary Safeguards
- **Untrusted Data Boundary**: All document contents are flagged as untrusted external text. Prevents arbitrary code execution, permission escalation, or system instruction overrides.
- **Citation Metadata Integrity**: Retains `chunk_id`, `document_id`, `source_filename`, `category`, `page_number`, and `effective_date` for downstream citation linking (`[DOC-{doc_id}-p{page}#chunk{seq}]`).
- **Resilient Fallback**: Operates smoothly via a built-in enterprise corpus if Qdrant vector storage is offline or unavailable.
- **Timeout Enforcement**: Bounded by a **3.0 second timeout**.
