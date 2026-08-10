"""
SQL Model Context Protocol (MCP) Server Implementation

Provides controlled, read-only SQL capabilities over allowlisted business tables
with SQLGlot AST security validation, query timeouts, row limits, and structured audit logging.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import logger
from app.mcp.schemas import (
    ExecuteSQLRequest,
    SQLQueryResult,
    TableSchemaRequest,
    TableSchemaResponse,
)
from app.mcp.sql_validator import (
    validate_and_enforce_sql,
    SQLSecurityError,
    ALLOWLISTED_TABLES,
)

# Detailed schema definitions for allowlisted tables
TABLE_SCHEMAS_DDL: Dict[str, Dict[str, Any]] = {
    "orders": {
        "table_name": "orders",
        "description": "Customer purchase orders and status tracking.",
        "columns": [
            {"name": "order_id", "type": "UUID", "primary_key": True},
            {"name": "customer_id", "type": "UUID", "nullable": False},
            {"name": "order_date", "type": "TIMESTAMP", "nullable": False},
            {"name": "status", "type": "VARCHAR(50)", "description": "pending, shipped, delivered, cancelled, returned"},
            {"name": "total_amount", "type": "DECIMAL(12,2)", "nullable": False},
            {"name": "carrier_id", "type": "VARCHAR(50)", "foreign_key": "carriers.carrier_id"},
            {"name": "warehouse_id", "type": "VARCHAR(50)", "foreign_key": "inventory.warehouse_id"},
        ],
    },
    "shipments": {
        "table_name": "shipments",
        "description": "Logistics shipment events and transit metrics.",
        "columns": [
            {"name": "shipment_id", "type": "UUID", "primary_key": True},
            {"name": "order_id", "type": "UUID", "foreign_key": "orders.order_id"},
            {"name": "carrier_id", "type": "VARCHAR(50)", "foreign_key": "carriers.carrier_id"},
            {"name": "shipped_at", "type": "TIMESTAMP", "nullable": False},
            {"name": "estimated_delivery", "type": "TIMESTAMP", "nullable": False},
            {"name": "actual_delivery", "type": "TIMESTAMP", "nullable": True},
            {"name": "shipping_cost", "type": "DECIMAL(10,2)", "nullable": False},
            {"name": "status", "type": "VARCHAR(50)", "description": "in_transit, delivered, delayed, lost"},
        ],
    },
    "returns": {
        "table_name": "returns",
        "description": "Product return logs and refund financial impacts.",
        "columns": [
            {"name": "return_id", "type": "UUID", "primary_key": True},
            {"name": "order_id", "type": "UUID", "foreign_key": "orders.order_id"},
            {"name": "reason", "type": "VARCHAR(100)", "description": "damaged, late_delivery, wrong_item, customer_remorse"},
            {"name": "refund_amount", "type": "DECIMAL(10,2)", "nullable": False},
            {"name": "returned_at", "type": "TIMESTAMP", "nullable": False},
            {"name": "warehouse_id", "type": "VARCHAR(50)", "foreign_key": "inventory.warehouse_id"},
        ],
    },
    "inventory": {
        "table_name": "inventory",
        "description": "Warehouse inventory stock levels and scrap write-offs.",
        "columns": [
            {"name": "item_id", "type": "VARCHAR(50)", "primary_key": True},
            {"name": "warehouse_id", "type": "VARCHAR(50)", "nullable": False},
            {"name": "product_name", "type": "VARCHAR(100)", "nullable": False},
            {"name": "stock_level", "type": "INTEGER", "nullable": False},
            {"name": "reorder_point", "type": "INTEGER", "nullable": False},
            {"name": "scrap_value_usd", "type": "DECIMAL(10,2)", "default": 0.0},
            {"name": "last_updated", "type": "TIMESTAMP", "nullable": False},
        ],
    },
    "suppliers": {
        "table_name": "suppliers",
        "description": "Supplier directory and performance metrics.",
        "columns": [
            {"name": "supplier_id", "type": "VARCHAR(50)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)", "nullable": False},
            {"name": "category", "type": "VARCHAR(50)", "nullable": False},
            {"name": "rating", "type": "DECIMAL(3,2)", "nullable": True},
            {"name": "lead_time_days", "type": "INTEGER", "nullable": False},
            {"name": "contract_status", "type": "VARCHAR(50)", "description": "active, under_review, terminated"},
        ],
    },
    "carriers": {
        "table_name": "carriers",
        "description": "Logistics carrier SLA terms and surcharge rules.",
        "columns": [
            {"name": "carrier_id", "type": "VARCHAR(50)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)", "nullable": False},
            {"name": "sla_threshold_percent", "type": "DECIMAL(5,2)", "default": 95.0},
            {"name": "contract_penalty_per_delay_usd", "type": "DECIMAL(10,2)", "default": 50.0},
            {"name": "peak_surcharge_enabled", "type": "BOOLEAN", "default": False},
        ],
    },
}


class SQLMCPServer:
    """
    Model Context Protocol (MCP) Server for SQL query execution and schema inspection.
    Enforces strict read-only access, AST validation, row limits, timeouts, and audit logging.
    """

    def __init__(self, db_engine: Optional[Any] = None):
        """
        Initializes the SQL MCP Server.
        Optionally accepts a custom SQLAlchemy engine (e.g. SQLite for testing/standalone mode).
        """
        self._db_engine = db_engine

    def get_table_schemas(self, request: Optional[TableSchemaRequest] = None) -> TableSchemaResponse:
        """
        Retrieves DDL summaries and schema context for allowlisted database tables.
        """
        target_table = request.table_name.lower() if request and request.table_name else None

        if target_table:
            if target_table not in ALLOWLISTED_TABLES:
                logger.warning(
                    "sql_mcp_unauthorized_schema_access_attempt",
                    requested_table=target_table,
                )
                return TableSchemaResponse(
                    success=False,
                    allowlisted_tables=sorted(list(ALLOWLISTED_TABLES)),
                    error=f"Table '{target_table}' is not authorized. Allowed tables: {sorted(list(ALLOWLISTED_TABLES))}.",
                )

            requested_schemas = {target_table: TABLE_SCHEMAS_DDL[target_table]}
        else:
            requested_schemas = TABLE_SCHEMAS_DDL

        return TableSchemaResponse(
            success=True,
            schemas=requested_schemas,
            allowlisted_tables=sorted(list(ALLOWLISTED_TABLES)),
        )

    async def execute_read_only_sql(
        self,
        request: ExecuteSQLRequest,
        timeout_seconds: float = 5.0,
    ) -> SQLQueryResult:
        """
        Validates and executes a read-only SQL query.
        Steps:
        1. Validate SQL via AST inspection (SQLGlot)
        2. Enforce row limits & SELECT-only permissions
        3. Execute against read-only database boundary with timeout enforcement
        4. Structured audit logging & safe result formatting
        """
        start_time = time.perf_counter()
        raw_query = request.sql_query
        task_id = request.task_id

        # Step 1: SQLGlot AST Safety & Policy Validation
        try:
            sanitized_sql, tables_accessed = validate_and_enforce_sql(raw_query, max_rows=100)
        except SQLSecurityError as sec_err:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(
                "sql_mcp_security_rejection",
                task_id=task_id,
                query=raw_query,
                error=str(sec_err),
                duration_ms=duration_ms,
            )
            return SQLQueryResult(
                success=False,
                sql_query=raw_query,
                error=str(sec_err),
                execution_time_ms=duration_ms,
            )
        except Exception as parse_err:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "sql_mcp_parse_error",
                task_id=task_id,
                query=raw_query,
                error=str(parse_err),
                duration_ms=duration_ms,
            )
            return SQLQueryResult(
                success=False,
                sql_query=raw_query,
                error=f"SQL Parsing Failure: {str(parse_err)}",
                execution_time_ms=duration_ms,
            )

        # Step 2: Query Execution under Database Access Boundary & Timeout
        try:
            result_data = await asyncio.wait_for(
                self._run_query_async(sanitized_sql),
                timeout=timeout_seconds,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            columns = result_data.get("columns", [])
            rows = result_data.get("rows", [])
            row_count = len(rows)

            # Audit Logging
            logger.info(
                "sql_mcp_query_success",
                task_id=task_id,
                sanitized_sql=sanitized_sql,
                tables_accessed=sorted(list(tables_accessed)),
                row_count=row_count,
                duration_ms=duration_ms,
            )

            return SQLQueryResult(
                success=True,
                sql_query=sanitized_sql,
                columns=columns,
                rows=rows,
                row_count=row_count,
                execution_time_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "sql_mcp_query_timeout",
                task_id=task_id,
                sql_query=sanitized_sql,
                timeout_seconds=timeout_seconds,
                duration_ms=duration_ms,
            )
            return SQLQueryResult(
                success=False,
                sql_query=sanitized_sql,
                error=f"Query execution timed out after {timeout_seconds} seconds.",
                execution_time_ms=duration_ms,
            )
        except Exception as db_err:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            # Mask internal database connection details/credentials safely
            safe_error_msg = self._sanitize_db_error(str(db_err))
            logger.error(
                "sql_mcp_execution_error",
                task_id=task_id,
                sql_query=sanitized_sql,
                error=safe_error_msg,
                duration_ms=duration_ms,
            )
            return SQLQueryResult(
                success=False,
                sql_query=sanitized_sql,
                error=f"Database Execution Error: {safe_error_msg}",
                execution_time_ms=duration_ms,
            )

    async def _run_query_async(self, sql_query: str) -> Dict[str, Any]:
        """
        Executes query against current database engine in a thread pool.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._execute_sync, sql_query)

    def _execute_sync(self, sql_query: str) -> Dict[str, Any]:
        """Synchronous query execution helper."""
        if self._db_engine is not None:
            engine = self._db_engine
        else:
            # Construct read-only connection string from settings
            engine = create_engine(
                settings.database_url_sync,
                connect_args={"options": "-c statement_timeout=5000ms"} if "postgresql" in settings.database_url_sync else {},
                pool_pre_ping=True,
            )

        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            columns = list(result.keys()) if result.returns_rows else []
            rows = [dict(row._mapping) for row in result.fetchall()] if result.returns_rows else []

        return {"columns": columns, "rows": rows}

    @staticmethod
    def _sanitize_db_error(raw_error: str) -> str:
        """Strips credentials, connection strings, or host details from database error messages."""
        lines = raw_error.split("\n")
        first_line = lines[0] if lines else raw_error
        # Remove passwords or credentials if present
        sanitized = first_line.split("://")[-1] if "://" in first_line else first_line
        if "@" in sanitized:
            sanitized = sanitized.split("@")[-1]
        return sanitized.strip()
