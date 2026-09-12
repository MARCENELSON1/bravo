"""Tiempos de servicio (coursing): el curso es del plato; la cocina cocina un
curso a la vez; el mozo dispara el siguiente."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import (
    EmptyOrder,
    InvalidItemTransition,
    ItemNotPending,
    NoCourseToFire,
)
from app.domain.order.value_objects import (
    Course,
    CourseState,
    ItemStatus,
    OrderStatus,
    Station,
)
from app.domain.shared.money import Money

_NOW = datetime(2026, 9, 5, 21, 0, tzinfo=UTC)


def _order() -> Order:
    return Order(id=str(uuid4()), tenant_id="t1", table_id="tb1", waiter_id="w1", currency="ARS")


def _plate(name: str, course: Course, station: Station = Station.KITCHEN) -> OrderItem:
    return OrderItem(
        id=str(uuid4()),
        product_id=f"p-{name}",
        name=name,
        unit_price=Money(1000, "ARS"),
        quantity=1,
        station=station,
        course=course,
    )


def _statuses(order: Order) -> dict[str, ItemStatus]:
    return {it.name: it.status for it in order.items}


def test_march_fires_starter_and_bar_holds_main_and_dessert() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.add_item(_plate("flan", Course.DESSERT))
    o.add_item(_plate("malbec", Course.IMMEDIATE, Station.BAR))
    fired = o.march(_NOW)
    assert {it.name for it in fired} == {"provoleta", "malbec"}
    st = _statuses(o)
    assert st["provoleta"] is ItemStatus.SENT
    assert st["malbec"] is ItemStatus.SENT
    assert st["bife"] is ItemStatus.HELD
    assert st["flan"] is ItemStatus.HELD
    assert o.status is OrderStatus.SENT  # HELD rolls up as "in kitchen"
    assert o.active_course() is Course.STARTER
    assert o.next_held_course() is Course.MAIN


def test_march_without_starter_starts_with_main() -> None:
    o = _order()
    o.add_item(_plate("bife", Course.MAIN))
    o.add_item(_plate("flan", Course.DESSERT))
    fired = o.march(_NOW)
    assert [it.name for it in fired] == ["bife"]
    assert _statuses(o)["flan"] is ItemStatus.HELD
    assert o.active_course() is Course.MAIN


def test_fire_next_course_after_starter_served() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.march(_NOW)
    o.advance_course(Course.STARTER, "preparing")
    o.advance_course(Course.STARTER, "ready", _NOW)
    assert o.course_state(Course.STARTER) is CourseState.READY
    o.advance_course(Course.STARTER, "served")
    assert o.course_state(Course.STARTER) is CourseState.SERVED
    assert o.active_course() is None  # nothing in flight → the table is ready
    fired = o.fire_next_course(_NOW)
    assert [it.name for it in fired] == ["bife"]
    assert o.course_state(Course.MAIN) is CourseState.IN_KITCHEN
    assert o.next_held_course() is None
    with pytest.raises(NoCourseToFire):
        o.fire_next_course(_NOW)


def test_fire_next_course_takes_pending_plate_of_same_course_along() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.march(_NOW)
    o.add_item(_plate("milanesa", Course.MAIN))  # pedida después, sin marchar
    fired = o.fire_next_course(_NOW)
    assert {it.name for it in fired} == {"bife", "milanesa"}


def test_new_round_while_lower_course_in_flight_is_held() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.march(_NOW)
    o.add_item(_plate("flan", Course.DESSERT))
    fired = o.march(_NOW)  # la entrada sigue al fuego → el postre espera
    assert fired == []
    assert _statuses(o)["flan"] is ItemStatus.HELD


def test_march_all_courses_fires_everything() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.add_item(_plate("flan", Course.DESSERT))
    fired = o.march(_NOW, coursing=False)
    assert len(fired) == 3
    assert all(it.status is ItemStatus.SENT for it in o.items)


def test_fire_all_fires_pending_and_held() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.march(_NOW)
    o.add_item(_plate("flan", Course.DESSERT))
    fired = o.fire_all(_NOW)  # "traé todo junto"
    assert {it.name for it in fired} == {"bife", "flan"}
    assert all(it.status is ItemStatus.SENT for it in o.items)
    with pytest.raises(EmptyOrder):
        o.fire_all(_NOW)


def test_advance_course_ready_only_fired_plates_of_that_course_and_station() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("rabas", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.add_item(_plate("malbec", Course.IMMEDIATE, Station.BAR))
    o.march(_NOW)
    o.advance_course(Course.STARTER, "preparing", station=Station.KITCHEN)
    ready = o.advance_course(Course.STARTER, "ready", _NOW, station=Station.KITCHEN)
    assert {it.name for it in ready} == {"provoleta", "rabas"}
    assert _statuses(o)["bife"] is ItemStatus.HELD  # no lo tocó
    assert _statuses(o)["malbec"] is ItemStatus.SENT  # otra estación
    with pytest.raises(InvalidItemTransition):
        o.advance_course(Course.MAIN, "ready", _NOW)  # nada al fuego en ese curso


def test_course_state_precedence_cooking_over_ready_over_held() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("rabas", Course.STARTER))
    o.march(_NOW)
    o.advance_course(Course.STARTER, "preparing")
    o.advance_item(o.items[0].id, "ready", _NOW)  # una lista, otra cocinando
    assert o.course_state(Course.STARTER) is CourseState.IN_KITCHEN
    o.advance_item(o.items[1].id, "ready", _NOW)
    assert o.course_state(Course.STARTER) is CourseState.READY
    assert o.course_state(Course.DESSERT) is None


def test_set_item_course_override_only_before_fire() -> None:
    o = _order()
    prov = _plate("provoleta", Course.STARTER)
    o.add_item(prov)
    o.set_item_course(prov.id, Course.MAIN)  # "la provoleta como principal"
    assert prov.course is Course.MAIN
    o.march(_NOW)
    with pytest.raises(ItemNotPending):
        o.set_item_course(prov.id, Course.STARTER)


def test_held_plates_block_order_level_ready() -> None:
    o = _order()
    o.add_item(_plate("provoleta", Course.STARTER))
    o.add_item(_plate("bife", Course.MAIN))
    o.march(_NOW)
    o.advance_course(Course.STARTER, "preparing")
    o.advance_course(Course.STARTER, "ready", _NOW)
    # La entrada está lista pero el principal está en espera: la ORDEN no está
    # "lista" (eso es por curso); sigue en cocina.
    assert o.status is OrderStatus.SENT
    assert o.course_state(Course.STARTER) is CourseState.READY
