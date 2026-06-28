from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.cashier.entities import CashCount, CashSession
from app.domain.cashier.exceptions import CashSessionAlreadyClosed
from app.domain.cashier.value_objects import CashSessionStatus
from app.domain.payment.value_objects import PaymentMethod
from app.domain.shared.money import Money

_NOW = datetime(2026, 6, 28, 23, 0, tzinfo=UTC)


def _session() -> CashSession:
    return CashSession(
        id=str(uuid4()),
        tenant_id="t1",
        opened_by="u1",
        opening_float=Money(50000, "ARS"),
        currency="ARS",
        opened_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
    )


def test_count_difference_is_signed() -> None:
    short = CashCount(PaymentMethod.CASH, Money(100000, "ARS"), Money(98000, "ARS"))
    over = CashCount(PaymentMethod.CARD, Money(50000, "ARS"), Money(50000, "ARS"))
    assert short.difference_amount == -2000  # faltante
    assert over.difference_amount == 0


def test_close_records_counts_and_closes() -> None:
    session = _session()
    counts = [
        CashCount(PaymentMethod.CASH, Money(150000, "ARS"), Money(149000, "ARS")),
    ]
    session.close(counts, _NOW, closed_by="u1", note="turno noche")
    assert session.status is CashSessionStatus.CLOSED
    assert session.closed_at == _NOW
    assert session.closed_by == "u1"
    assert session.note == "turno noche"
    assert session.counts[0].difference_amount == -1000


def test_cannot_close_twice() -> None:
    session = _session()
    session.close([], _NOW, closed_by="u1")
    with pytest.raises(CashSessionAlreadyClosed):
        session.close([], _NOW, closed_by="u1")
