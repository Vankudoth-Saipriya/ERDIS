"""
Unit Tests for SQL AST Security Validation Module
Targeted security tests covering all 17 required AST validation and policy enforcement rules.
"""

import pytest
from app.mcp.sql_validator import validate_and_enforce_sql, SQLSecurityError


def test_valid_select_query():
    """Test 1: Valid SELECT query against allowlisted table passes validation."""
    query = "SELECT order_id, customer_id, total_amount FROM orders WHERE status = 'delivered'"
    sanitized_sql, tables = validate_and_enforce_sql(query)
    assert "orders" in tables
    assert "LIMIT 100" in sanitized_sql
    assert "SELECT" in sanitized_sql


def test_insert_rejection():
    """Test 2: INSERT statement is strictly rejected."""
    query = "INSERT INTO orders (customer_id, total_amount) VALUES ('c1', 100.00)"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_update_rejection():
    """Test 3: UPDATE statement is strictly rejected."""
    query = "UPDATE orders SET status = 'cancelled' WHERE order_id = 'o1'"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_delete_rejection():
    """Test 4: DELETE statement is strictly rejected."""
    query = "DELETE FROM orders WHERE status = 'pending'"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_drop_rejection():
    """Test 5: DROP TABLE statement is strictly rejected."""
    query = "DROP TABLE orders"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_alter_rejection():
    """Test 6: ALTER TABLE statement is strictly rejected."""
    query = "ALTER TABLE orders ADD COLUMN malicious_col VARCHAR(100)"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_create_rejection():
    """Test 7: CREATE TABLE statement is strictly rejected."""
    query = "CREATE TABLE hacked_table (id INT PRIMARY KEY)"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_truncate_rejection():
    """Test 8: TRUNCATE TABLE statement is strictly rejected."""
    query = "TRUNCATE TABLE orders"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Only SELECT queries are permitted" in str(exc_info.value)


def test_multiple_statement_rejection():
    """Test 9: Multi-statement queries separated by semicolons are strictly rejected."""
    query = "SELECT * FROM orders; DROP TABLE shipments;"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "Multi-statement execution" in str(exc_info.value)


def test_unauthorized_table_rejection():
    """Test 10: Queries targeting unauthorized tables or system schemas are rejected."""
    query_users = "SELECT * FROM users WHERE role = 'admin'"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query_users)
    assert "Access to table(s) ['users'] is not authorized" in str(exc_info.value)

    query_sys = "SELECT * FROM pg_catalog.pg_tables"
    with pytest.raises(SQLSecurityError) as exc_info_sys:
        validate_and_enforce_sql(query_sys)
    assert "not authorized" in str(exc_info_sys.value)


def test_cartesian_join_rejection():
    """Test 11: Unrestricted Cartesian joins (JOIN without ON/USING or CROSS JOIN) are rejected."""
    # Implicit comma join
    query_comma = "SELECT * FROM orders, shipments"
    with pytest.raises(SQLSecurityError) as exc_info1:
        validate_and_enforce_sql(query_comma)
    assert "Cartesian JOINs" in str(exc_info1.value)

    # Explicit JOIN without ON/USING
    query_no_on = "SELECT * FROM orders JOIN shipments"
    with pytest.raises(SQLSecurityError) as exc_info2:
        validate_and_enforce_sql(query_no_on)
    assert "Cartesian JOINs" in str(exc_info2.value)

    # CROSS JOIN
    query_cross = "SELECT * FROM orders CROSS JOIN shipments"
    with pytest.raises(SQLSecurityError) as exc_info3:
        validate_and_enforce_sql(query_cross)
    assert "Cartesian JOINs" in str(exc_info3.value)


def test_row_limit_enforcement():
    """Test 12: Row limit is automatically appended or capped to max 100 rows."""
    # Query with no limit -> limit 100 enforced
    q1 = "SELECT * FROM orders"
    sanitized1, _ = validate_and_enforce_sql(q1)
    assert "LIMIT 100" in sanitized1

    # Query with limit > 100 -> capped to 100
    q2 = "SELECT * FROM orders LIMIT 500"
    sanitized2, _ = validate_and_enforce_sql(q2)
    assert "LIMIT 100" in sanitized2

    # Query with limit <= 100 -> preserved
    q3 = "SELECT * FROM orders LIMIT 25"
    sanitized3, _ = validate_and_enforce_sql(q3)
    assert "LIMIT 25" in sanitized3


def test_malformed_sql_syntax():
    """Test 14: Malformed SQL syntax triggers a parsing security exception."""
    query = "SELECT FROM WHERE status ="
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "SQL Syntax Parsing Failure" in str(exc_info.value)


def test_nested_subquery_security():
    """Test 15: Valid subquery passes; subquery with unauthorized tables or mutations fails."""
    # Valid subquery against allowlisted tables
    valid_subquery = "SELECT * FROM orders WHERE carrier_id IN (SELECT carrier_id FROM carriers WHERE sla_threshold_percent >= 90.0)"
    sanitized, tables = validate_and_enforce_sql(valid_subquery)
    assert "orders" in tables
    assert "carriers" in tables

    # Subquery targeting unauthorized table
    unauth_subquery = "SELECT * FROM orders WHERE customer_id IN (SELECT user_id FROM external_users)"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(unauth_subquery)
    assert "external_users" in str(exc_info.value)


def test_union_query_security():
    """Test 16: Valid UNION queries pass; UNION targeting unauthorized tables fails."""
    valid_union = "SELECT carrier_id FROM orders UNION SELECT carrier_id FROM shipments"
    sanitized, tables = validate_and_enforce_sql(valid_union)
    assert "orders" in tables
    assert "shipments" in tables

    unauth_union = "SELECT carrier_id FROM orders UNION SELECT id FROM internal_auth"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(unauth_union)
    assert "internal_auth" in str(exc_info.value)


def test_comment_bypass_prevention():
    """Test 17: Comments cannot bypass AST multi-statement or keyword rejection."""
    comment_multi = "SELECT * FROM orders; -- DROP TABLE shipments;\n DROP TABLE carriers;"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(comment_multi)
    assert "Multi-statement execution" in str(exc_info.value)

    # Valid query with comments parses safely
    comment_valid = "SELECT * FROM orders /* inline comment */ WHERE status = 'delivered'"
    sanitized, tables = validate_and_enforce_sql(comment_valid)
    assert "orders" in tables


def test_cte_alias_spoofing_prevention():
    """Regression Test: CTE alias cannot spoof/mask unauthorized physical table names."""
    query = "WITH users AS (SELECT * FROM users) SELECT * FROM users"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_enforce_sql(query)
    assert "users" in str(exc_info.value)


def test_schema_qualification_rejection():
    """Regression Test: Non-public schema qualification (pg_catalog, information_schema) is rejected."""
    query_pg = "SELECT * FROM pg_catalog.pg_tables"
    with pytest.raises(SQLSecurityError) as exc_info1:
        validate_and_enforce_sql(query_pg)
    assert "not authorized" in str(exc_info1.value)

    query_info = "SELECT * FROM information_schema.tables"
    with pytest.raises(SQLSecurityError) as exc_info2:
        validate_and_enforce_sql(query_info)
    assert "not authorized" in str(exc_info2.value)


def test_valid_analytical_sql():
    """Test Analytical SQL: Complex aggregations, GROUP BY, HAVING, and JOIN with ON clause."""
    query = """
    SELECT
        o.carrier_id,
        COUNT(o.order_id) AS total_orders,
        SUM(o.total_amount) AS revenue,
        AVG(c.sla_threshold_percent) AS avg_sla
    FROM orders o
    JOIN carriers c ON o.carrier_id = c.carrier_id
    WHERE o.status = 'delivered'
    GROUP BY o.carrier_id
    HAVING COUNT(o.order_id) > 2
    ORDER BY revenue DESC
    """
    sanitized, tables = validate_and_enforce_sql(query)
    assert "orders" in tables
    assert "carriers" in tables
    assert "GROUP BY" in sanitized
    assert "HAVING" in sanitized
    assert "LIMIT 100" in sanitized
