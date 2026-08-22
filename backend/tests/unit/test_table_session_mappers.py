"""Unit: round-trip de los mappers de la sesión de mesa (cimiento table_sessions)."""

from datetime import UTC, datetime

from app.domain.table_session.entities import Sector, TableSession
from app.domain.table_session.value_objects import SessionOrigin, SessionStatus
from app.infrastructure.persistence.mappers import (
    sector_to_domain,
    sector_to_orm,
    table_session_to_domain,
    table_session_to_orm,
)


def test_table_session_roundtrip():
    s = TableSession(
        id="s1",
        tenant_id="t1",
        table_id="tb1",
        pax=4,
        waiter_id="w1",
        opened_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    back = table_session_to_domain(table_session_to_orm(s))
    assert back.id == "s1"
    assert back.pax == 4
    assert back.waiter_id == "w1"
    assert back.status is SessionStatus.OPEN
    assert back.origin is SessionOrigin.SALON


def test_sector_roundtrip():
    back = sector_to_domain(
        sector_to_orm(Sector(id="x", tenant_id="t1", name="Terraza", color="#0f0", sort_order=2))
    )
    assert back.name == "Terraza"
    assert back.color == "#0f0"
    assert back.sort_order == 2
