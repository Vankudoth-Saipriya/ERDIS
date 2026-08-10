"""
SQL AST Security Validation Module using SQLGlot
"""

from typing import Set, Tuple
import sqlglot
import sqlglot.expressions as exp

ALLOWLISTED_TABLES: Set[str] = {
    "orders",
    "shipments",
    "returns",
    "inventory",
    "suppliers",
    "carriers",
}

FORBIDDEN_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Grant,
    exp.Revoke,
    exp.Command,
    exp.Merge,
    exp.Copy,
    exp.Pragma,
)

FORBIDDEN_SCHEMAS: Set[str] = {
    "pg_catalog",
    "information_schema",
    "pg_toast",
    "sys",
    "system",
}


class SQLSecurityError(Exception):
    """Raised when a SQL query violates security policies."""
    pass


def _extract_physical_tables(expression: exp.Expression) -> Set[str]:
    """
    Accurately extracts all physical tables accessed in the query AST.
    Distinguishes real physical tables from temporary CTE aliases, avoiding
    CTE alias spoofing bypasses (e.g., 'WITH users AS (SELECT * FROM users)').
    """
    physical_tables: Set[str] = set()
    defined_ctes: Set[str] = set()

    # 1. Process CTE bodies
    for cte in expression.find_all(exp.CTE):
        cte_name = cte.alias.lower() if cte.alias else ""
        if cte.this:
            for table_expr in cte.this.find_all(exp.Table):
                table_name = table_expr.name.lower() if table_expr.name else ""
                schema_name = table_expr.db.lower() if table_expr.db else ""
                if schema_name and schema_name not in ("", "public"):
                    raise SQLSecurityError(f"Forbidden: Access to schema '{schema_name}' is not authorized.")
                if table_name and table_name not in defined_ctes:
                    physical_tables.add(table_name)
        if cte_name:
            defined_ctes.add(cte_name)

    # 2. Process main query body outside CTE definitions
    for table_expr in expression.find_all(exp.Table):
        if table_expr.find_ancestor(exp.CTE) is None:
            table_name = table_expr.name.lower() if table_expr.name else ""
            schema_name = table_expr.db.lower() if table_expr.db else ""
            if schema_name and schema_name not in ("", "public"):
                raise SQLSecurityError(f"Forbidden: Access to schema '{schema_name}' is not authorized.")
            if table_name and table_name not in defined_ctes:
                physical_tables.add(table_name)

    return physical_tables


def validate_and_enforce_sql(sql_query: str, max_rows: int = 100) -> Tuple[str, Set[str]]:
    """
    Parses and validates a SQL query using SQLGlot AST inspection.
    Enforces SELECT-only execution, table allowlists, Cartesian join rejection,
    and row limit enforcement.

    Returns:
        Tuple[str, Set[str]]: (Sanitized and limit-enforced SQL query string, Set of accessed tables)
    """
    if not sql_query or not sql_query.strip():
        raise SQLSecurityError("Query string cannot be empty.")

    # 1. Multi-statement Check
    try:
        parsed_statements = sqlglot.parse(sql_query, read="postgres")
    except Exception as err:
        raise SQLSecurityError(f"SQL Syntax Parsing Failure: {str(err)}")

    # Filter out empty statements resulting from trailing semicolons
    valid_statements = [stmt for stmt in parsed_statements if stmt is not None]
    if len(valid_statements) > 1:
        raise SQLSecurityError("Forbidden: Multi-statement execution (multiple semicolons) is prohibited.")

    if not valid_statements:
        raise SQLSecurityError("Query string contains no valid SQL statements.")

    expression = valid_statements[0]

    # 2. Reject non-SELECT & Mutation Expressions
    if not isinstance(expression, exp.Query):
        raise SQLSecurityError("Forbidden: Only SELECT queries are permitted.")

    # Check for any nested mutation or forbidden expressions
    for forbidden_type in FORBIDDEN_EXPRESSION_TYPES:
        if list(expression.find_all(forbidden_type)):
            forbidden_name = forbidden_type.__name__.upper()
            raise SQLSecurityError(f"Forbidden: Nested data modification keyword '{forbidden_name}' detected.")

    # 3. Table Allowlist & Schema Check
    tables_accessed = _extract_physical_tables(expression)

    unauthorized_tables = tables_accessed - ALLOWLISTED_TABLES
    if unauthorized_tables:
        raise SQLSecurityError(
            f"Forbidden: Access to table(s) {sorted(list(unauthorized_tables))} is not authorized. "
            f"Allowed tables: {sorted(list(ALLOWLISTED_TABLES))}."
        )

    # 4. Cartesian Join Check (Rejects JOIN without ON or USING clause, or CROSS JOIN)
    for join_expr in expression.find_all(exp.Join):
        has_on = join_expr.args.get("on") is not None
        has_using = join_expr.args.get("using") is not None
        is_cross_join = join_expr.kind and join_expr.kind.upper() == "CROSS"

        if is_cross_join or (not has_on and not has_using):
            raise SQLSecurityError("Forbidden: Unrestricted Cartesian JOINs without ON or USING clause are prohibited.")

    # 5. Row Limit Enforcement (Enforce max 100 rows)
    limit_expr = expression.args.get("limit")
    if limit_expr is None:
        expression = expression.limit(max_rows)
    else:
        try:
            current_limit = int(limit_expr.expression.this)
            if current_limit > max_rows:
                expression = expression.limit(max_rows)
        except (ValueError, AttributeError):
            expression = expression.limit(max_rows)

    sanitized_sql = expression.sql(dialect="postgres")
    return sanitized_sql, tables_accessed
