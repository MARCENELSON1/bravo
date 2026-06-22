"""Deterministic SQL guardrail (the security core). Parses the LLM's SQL with
sqlglot and accepts ONLY a safe read query: a single SELECT, no star, every
table/column inside the curated allow-list, no system catalogs, no dangerous
functions; injects/caps a LIMIT. Tenant isolation is NOT enforced here — that is
guaranteed at execution time by the read-only transaction + RLS. This layer
bounds WHAT can be read; RLS bounds WHOSE rows."""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp

from app.domain.copilot.exceptions import UnsafeQuery
from app.domain.copilot.schema import allowed_columns, is_allowed_table

# Custom functions that must never run (parse as exp.Anonymous).
_BANNED_FUNCTIONS = frozenset(
    {
        "pg_sleep", "pg_read_file", "pg_ls_dir", "pg_read_binary_file",
        "lo_import", "lo_export", "dblink", "dblink_exec", "copy",
        "current_setting", "set_config", "txid_current", "query_to_xml",
    }
)

DEFAULT_MAX_ROWS = 200


@dataclass(frozen=True)
class ValidatedSql:
    sql: str


def validate_sql(raw: str, *, max_rows: int = DEFAULT_MAX_ROWS) -> ValidatedSql:
    """Return the normalized, LIMIT-bounded SQL, or raise ``UnsafeQuery``."""
    try:
        statements = [s for s in sqlglot.parse(raw, read="postgres") if s is not None]
    except Exception as exc:  # noqa: BLE001 — any parse failure is unsafe
        raise UnsafeQuery("No pudimos interpretar la consulta.") from exc

    if len(statements) != 1:
        raise UnsafeQuery("La consulta debe ser una sola sentencia de lectura.")
    statement = statements[0]
    if not isinstance(statement, exp.Select):
        raise UnsafeQuery("Solo se permiten consultas de lectura (SELECT).")

    _reject_star(statement)
    referenced = _check_tables(statement)
    _check_columns(statement, referenced)
    _check_functions(statement)

    return ValidatedSql(_with_limit(statement, max_rows).sql(dialect="postgres"))


def _reject_star(statement: exp.Select) -> None:
    # Reject "SELECT *" / "t.*" in any (sub)select projection. count(*) is fine
    # because there the Star is nested inside a function, not a projection.
    for select in statement.find_all(exp.Select):
        for projection in select.expressions:
            if isinstance(projection, exp.Star) or (
                isinstance(projection, exp.Column) and isinstance(projection.this, exp.Star)
            ):
                raise UnsafeQuery("Especificá las columnas (no se permite SELECT *).")


def _check_tables(statement: exp.Select) -> set[str]:
    referenced: set[str] = set()
    for table in statement.find_all(exp.Table):
        name = table.name.lower()
        # table.db is the schema qualifier (e.g. pg_catalog.*, information_schema.*).
        if table.db or not is_allowed_table(name):
            raise UnsafeQuery(f"No se puede consultar la tabla '{table.name}'.")
        referenced.add(name)
    if not referenced:
        raise UnsafeQuery("La consulta no referencia tablas permitidas.")
    return referenced


def _check_columns(statement: exp.Select, referenced: set[str]) -> None:
    allowed: set[str] = set()
    for table in referenced:
        allowed |= set(allowed_columns(table))
    # Names introduced by the query itself (aliases, CTE names) are also allowed.
    aliases = {a.alias_or_name.lower() for a in statement.find_all(exp.Alias)}
    aliases |= {t.alias.lower() for t in statement.find_all(exp.Table) if t.alias}
    for column in statement.find_all(exp.Column):
        name = column.name.lower()
        if name and name not in allowed and name not in aliases:
            raise UnsafeQuery(f"No se puede usar la columna '{column.name}'.")


def _check_functions(statement: exp.Select) -> None:
    for func in statement.find_all(exp.Anonymous):
        if func.name.lower() in _BANNED_FUNCTIONS:
            raise UnsafeQuery("La consulta usa una función no permitida.")


def _with_limit(statement: exp.Select, max_rows: int) -> exp.Select:
    limit = statement.args.get("limit")
    current: int | None = None
    if limit is not None and isinstance(limit.expression, exp.Literal):
        if limit.expression.is_int:
            current = int(limit.expression.name)
    effective = max_rows if current is None else min(current, max_rows)
    return statement.limit(effective)
