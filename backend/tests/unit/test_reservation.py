from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.reservation.entities import Reservation
from app.domain.reservation.exceptions import (
    InvalidPartySize,
    InvalidReservationTransition,
)
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn

_AT = datetime(2026, 6, 21, 21, 0, tzinfo=UTC)


def _reservation(party_size: int = 2) -> Reservation:
    return Reservation(
        id="r1",
        tenant_id="t1",
        customer_name="Pérez",
        party_size=party_size,
        reserved_at=_AT,
        turn=ServiceTurn.DINNER,
    )


def test_reservation_starts_pending() -> None:
    reservation = _reservation()
    assert reservation.status is ReservationStatus.PENDING
    assert reservation.table_id is None


def test_rejects_non_positive_party_size() -> None:
    with pytest.raises(InvalidPartySize):
        _reservation(party_size=0)


def test_happy_path_confirm_seat_complete() -> None:
    reservation = _reservation()
    reservation.confirm()
    assert reservation.status is ReservationStatus.CONFIRMED
    reservation.seat()
    assert reservation.status is ReservationStatus.SEATED
    reservation.complete()
    assert reservation.status is ReservationStatus.COMPLETED


def test_seat_directly_from_pending() -> None:
    reservation = _reservation()
    reservation.seat()  # walk-in confirmed on arrival
    assert reservation.status is ReservationStatus.SEATED


def test_cancel_from_pending() -> None:
    reservation = _reservation()
    reservation.cancel()
    assert reservation.status is ReservationStatus.CANCELLED


def test_mark_no_show_from_confirmed() -> None:
    reservation = _reservation()
    reservation.confirm()
    reservation.mark_no_show()
    assert reservation.status is ReservationStatus.NO_SHOW


def test_complete_requires_seated() -> None:
    reservation = _reservation()
    reservation.confirm()
    with pytest.raises(InvalidReservationTransition):
        reservation.complete()  # not SEATED yet


def test_cannot_transition_from_terminal() -> None:
    reservation = _reservation()
    reservation.cancel()
    with pytest.raises(InvalidReservationTransition):
        reservation.confirm()
    with pytest.raises(InvalidReservationTransition):
        reservation.mark_no_show()


def test_confirm_twice_rejected() -> None:
    reservation = _reservation()
    reservation.confirm()
    with pytest.raises(InvalidReservationTransition):
        reservation.confirm()


def test_reschedule_updates_data() -> None:
    reservation = _reservation()
    new_at = datetime(2026, 6, 22, 13, 0, tzinfo=UTC)
    reservation.reschedule(
        reserved_at=new_at, turn=ServiceTurn.LUNCH, party_size=4, table_id="tbl1"
    )
    assert reservation.reserved_at == new_at
    assert reservation.turn is ServiceTurn.LUNCH
    assert reservation.party_size == 4
    assert reservation.table_id == "tbl1"


def test_reschedule_rejected_when_terminal() -> None:
    reservation = _reservation()
    reservation.cancel()
    with pytest.raises(InvalidReservationTransition):
        reservation.reschedule(
            reserved_at=_AT, turn=ServiceTurn.DINNER, party_size=2, table_id=None
        )


def test_reschedule_rejects_bad_party_size() -> None:
    reservation = _reservation()
    with pytest.raises(InvalidPartySize):
        reservation.reschedule(
            reserved_at=_AT, turn=ServiceTurn.DINNER, party_size=0, table_id=None
        )
