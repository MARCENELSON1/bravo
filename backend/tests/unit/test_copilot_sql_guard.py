from __future__ import annotations

import pytest

from app.domain.copilot.exceptions import UnsafeQuery
from app.domain.copilot.sql_guard import DEFAULT_MAX_ROWS, validate_sql


def test_accepts_simple_select() -> None:
    out = validate_sql("SELECT product_name, line_amount FROM sale_facts")
    assert "sale_facts" in out.sql.lower()
    assert "limit" in out.sql.lower()  # LIMIT injected


def test_accepts_aggregation_with_count_star() -> None:
    out = validate_sql(
        "SELECT category, count(*), sum(line_amount) FROM sale_facts GROUP BY category"
    )
    assert "count(*)" in out.sql.lower().replace(" ", "")


def test_accepts_join_between_allowed_tables() -> None:
    sql = (
        "SELECT o.status, oi.quantity FROM orders AS o "
        "JOIN order_items AS oi ON oi.order_id = o.id"
    )
    out = validate_sql(sql)
    assert "orders" in out.sql.lower()


def test_rejects_insert() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("INSERT INTO sale_facts (quantity) VALUES (1)")


def test_rejects_update_delete_drop() -> None:
    for bad in (
        "UPDATE payments SET amount = 0",
        "DELETE FROM payments",
        "DROP TABLE payments",
    ):
        with pytest.raises(UnsafeQuery):
            validate_sql(bad)


def test_rejects_multiple_statements() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT amount FROM payments; DROP TABLE payments")


def test_rejects_select_star() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT * FROM payments")


def test_rejects_table_outside_allowlist() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT email FROM users")


def test_rejects_column_outside_allowlist() -> None:
    # external_ref is a real payments column but NOT in the allow-list.
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT external_ref FROM payments")


def test_rejects_system_catalog() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT tablename FROM pg_catalog.pg_tables")
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT table_name FROM information_schema.tables")


def test_rejects_banned_function() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("SELECT pg_sleep(10) FROM sale_facts")


def test_injects_limit_when_missing() -> None:
    out = validate_sql("SELECT amount FROM payments")
    assert f"LIMIT {DEFAULT_MAX_ROWS}".lower() in out.sql.lower()


def test_caps_limit_when_too_high() -> None:
    out = validate_sql("SELECT amount FROM payments LIMIT 999999")
    assert f"LIMIT {DEFAULT_MAX_ROWS}".lower() in out.sql.lower()
    assert "999999" not in out.sql


def test_keeps_limit_under_max() -> None:
    out = validate_sql("SELECT amount FROM payments LIMIT 5")
    assert "limit 5" in out.sql.lower()


def test_rejects_unparseable() -> None:
    with pytest.raises(UnsafeQuery):
        validate_sql("not a query at all !!!")
