from __future__ import annotations

import pytest

from app.application.public_menu.use_cases import RequestTableAttention
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.public_menu.value_objects import TableCallKind
from app.domain.realtime.ports import DomainEvent
from app.domain.table.entities import Table
from app.domain.table.exceptions import TableNotFound
from app.infrastructure.public_menu.signed_table_qr import HmacTableQrToken
from tests.fakes import FakeTenantContext


class _FakeTables:
    def __init__(self, table: Table | None) -> None:
        self._table = table

    async def get_by_id(self, tenant_id: str, table_id: str) -> Table | None:
        return self._table


class _SpyBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)


def _use_case(table: Table | None, secret: str = "s3cr3t"):
    token = HmacTableQrToken(secret=secret)
    bus = _SpyBus()
    uc = RequestTableAttention(
        token=token,
        tables=_FakeTables(table),  # type: ignore[arg-type]
        event_bus=bus,  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
    )
    return uc, token, bus


async def test_call_waiter_publishes_floor_call_with_table_number() -> None:
    table = Table(id="tbl-1", tenant_id="t1", number=7)
    uc, token, bus = _use_case(table)

    await uc.execute(token=token.issue("t1", "tbl-1"), kind=TableCallKind.WAITER)

    assert len(bus.published) == 1
    event = bus.published[0]
    assert event.type == "floor.call"
    assert event.tenant_id == "t1"
    assert event.payload == {"table_id": "tbl-1", "table_number": "7", "kind": "waiter"}


async def test_request_bill_publishes_bill_kind() -> None:
    table = Table(id="tbl-1", tenant_id="t1", number=3)
    uc, token, bus = _use_case(table)

    await uc.execute(token=token.issue("t1", "tbl-1"), kind=TableCallKind.BILL)

    assert bus.published[0].payload["kind"] == "bill"


async def test_bad_token_rejected_and_nothing_published() -> None:
    uc, _token, bus = _use_case(Table(id="tbl-1", tenant_id="t1", number=1))
    with pytest.raises(InvalidTableQrToken):
        await uc.execute(token="garbage.deadbeef", kind=TableCallKind.WAITER)
    assert bus.published == []


async def test_missing_table_raises_and_nothing_published() -> None:
    uc, token, bus = _use_case(None)
    with pytest.raises(TableNotFound):
        await uc.execute(token=token.issue("t1", "tbl-1"), kind=TableCallKind.WAITER)
    assert bus.published == []
