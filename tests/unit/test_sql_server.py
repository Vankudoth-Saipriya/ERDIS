"""
Unit Tests for SQL MCP Server Implementation
Tests schema inspection, query execution, timeout enforcement, and credential isolation.
"""

import asyncio
import pytest
from sqlalchemy import create_engine, text

from app.mcp.schemas import ExecuteSQLRequest, TableSchemaRequest
from app.mcp.sql_server import SQLMCPServer, TABLE_SCHEMAS_DDL


@pytest.fixture
def in_memory_db_engine():
    """Provides an in-memory SQLite database populated with mock enterprise operational tables."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT,
                order_date TEXT,
                status TEXT,
                total_amount REAL,
                carrier_id TEXT,
                warehouse_id TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE carriers (
                carrier_id TEXT PRIMARY KEY,
                name TEXT,
                sla_threshold_percent REAL,
                contract_penalty_per_delay_usd REAL,
                peak_surcharge_enabled INTEGER
            );
        """))
        conn.execute(text("""
            INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, carrier_id, warehouse_id)
            VALUES
                ('ORD-001', 'CUST-101', '2025-09-01', 'delivered', 250.00, 'CARRIER-X', 'MIDWEST-01'),
                ('ORD-002', 'CUST-102', '2025-09-02', 'delayed', 180.50, 'CARRIER-X', 'MIDWEST-01'),
                ('ORD-003', 'CUST-103', '2025-09-03', 'shipped', 95.00, 'CARRIER-Y', 'WEST-02');
        """))
        conn.execute(text("""
            INSERT INTO carriers (carrier_id, name, sla_threshold_percent, contract_penalty_per_delay_usd, peak_surcharge_enabled)
            VALUES
                ('CARRIER-X', 'Logistics Partner X', 95.0, 50.0, 1),
                ('CARRIER-Y', 'Logistics Partner Y', 98.0, 75.0, 0);
        """))
        conn.commit()
    return engine


def test_get_all_table_schemas():
    """Verifies retrieval of all allowlisted table schemas."""
    server = SQLMCPServer()
    response = server.get_table_schemas()
    assert response.success is True
    assert len(response.schemas) == 6
    assert "orders" in response.schemas
    assert "carriers" in response.schemas
    assert "shipments" in response.schemas
    assert response.allowlisted_tables == sorted(["orders", "shipments", "returns", "inventory", "suppliers", "carriers"])


def test_get_single_table_schema():
    """Verifies schema retrieval for a specific table."""
    server = SQLMCPServer()
    request = TableSchemaRequest(table_name="orders")
    response = server.get_table_schemas(request)
    assert response.success is True
    assert "orders" in response.schemas
    assert len(response.schemas) == 1
    assert response.schemas["orders"]["table_name"] == "orders"


def test_get_unauthorized_table_schema():
    """Verifies rejection of unauthorized table schema requests."""
    server = SQLMCPServer()
    request = TableSchemaRequest(table_name="secret_financials")
    response = server.get_table_schemas(request)
    assert response.success is False
    assert "not authorized" in response.error


@pytest.mark.asyncio
async def test_execute_valid_sql_query(in_memory_db_engine):
    """Verifies execution of a valid read-only SQL query returning structured results."""
    server = SQLMCPServer(db_engine=in_memory_db_engine)
    request = ExecuteSQLRequest(
        sql_query="SELECT order_id, total_amount, status FROM orders WHERE status = 'delivered'",
        task_id="TASK-TEST-01",
    )
    result = await server.execute_read_only_sql(request)
    assert result.success is True
    assert result.row_count == 1
    assert result.columns == ["order_id", "total_amount", "status"]
    assert result.rows[0]["order_id"] == "ORD-001"
    assert result.rows[0]["status"] == "delivered"
    assert result.execution_time_ms >= 0.0
    assert result.query_id.startswith("SQL-")


@pytest.mark.asyncio
async def test_execute_security_violating_sql(in_memory_db_engine):
    """Verifies that security-violating queries fail before DB execution with structured error."""
    server = SQLMCPServer(db_engine=in_memory_db_engine)
    request = ExecuteSQLRequest(
        sql_query="DROP TABLE orders",
        task_id="TASK-TEST-02",
    )
    result = await server.execute_read_only_sql(request)
    assert result.success is False
    assert "Only SELECT queries are permitted" in result.error
    assert result.row_count == 0


@pytest.mark.asyncio
async def test_execute_query_timeout():
    """Test 13: Verifies timeout enforcement during query execution."""
    server = SQLMCPServer()

    # Mock _run_query_async to simulate a slow DB operation exceeding timeout
    async def mock_slow_query(sql):
        await asyncio.sleep(0.5)
        return {}

    server._run_query_async = mock_slow_query

    request = ExecuteSQLRequest(sql_query="SELECT * FROM orders", task_id="TASK-TIMEOUT")
    result = await server.execute_read_only_sql(request, timeout_seconds=0.1)

    assert result.success is False
    assert "timed out" in result.error


def test_sanitize_db_error():
    """Verifies that internal DB credentials and connection strings are masked from error messages."""
    raw_error = "OperationalError: connection to server at postgresql://erdis_user:secret_password@10.0.0.5:5432/erdis_db failed"
    sanitized = SQLMCPServer._sanitize_db_error(raw_error)
    assert "secret_password" not in sanitized
    assert "erdis_user" not in sanitized
