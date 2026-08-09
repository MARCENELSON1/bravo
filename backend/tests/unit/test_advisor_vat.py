"""Unit tests for IVA netting (Productos v3 Tanda 2B): net_of_vat and the
AdvisorKpis margins/ratios on a net basis, with sales/ticket kept gross."""

from __future__ import annotations

from app.domain.advisor.kpis import AdvisorKpis, net_of_vat


def _kpis(
    vat_bps: int,
    sales: int = 121000,
    food: int = 60500,
    food_net: int | None = None,
) -> AdvisorKpis:
    return AdvisorKpis(
        currency="ARS",
        period_days=30,
        sales_amount=sales,
        food_cost_amount=food,
        labor_cost_amount=0,
        other_fixed_amount=0,
        waste_amount=0,
        orders_count=10,
        average_ticket_amount=sales // 10,
        no_show_rate_bps=0,
        configured=True,
        vat_bps=vat_bps,
        food_cost_net_amount=food_net,
    )


def test_net_of_vat() -> None:
    assert net_of_vat(121000, 2100) == 100000  # 1210,00 con IVA → 1000,00 neto
    assert net_of_vat(60500, 2100) == 50000
    assert net_of_vat(121000, 0) == 121000  # sin cargar → identidad


def test_vat_off_keeps_gross_margins() -> None:
    k = _kpis(vat_bps=0)
    assert k.gross_margin_amount == 121000 - 60500  # paridad, todo bruto
    assert k.food_cost_ratio_bps == round(60500 * 10000 / 121000)


def test_vat_on_nets_margins_and_ratios() -> None:
    k = _kpis(vat_bps=2100)
    # ventas netas 100000, food neto 50000
    assert k.gross_margin_amount == 50000
    assert k.net_margin_amount == 50000  # sin labor/otros
    assert k.food_cost_ratio_bps == 5000  # 50000/100000 = 50%


def test_sales_and_ticket_stay_gross() -> None:
    k = _kpis(vat_bps=2100)
    # lo que ringea/paga el cliente queda bruto; solo los márgenes son netos.
    assert k.sales_amount == 121000
    assert k.average_ticket_amount == 12100


def test_stored_net_food_beats_global_renetting() -> None:
    # Solución 1 (F3): cuando la proyección guardó el food neto per-insumo, el
    # margen lo usa directo — NO re-netea el bruto global (que daría 50000). Esto
    # captura el caso monotributo (insumos sin IVA que no hay que netear).
    k = _kpis(vat_bps=2100, food=60500, food_net=40000)
    assert k._net_food_cost == 40000  # el neto guardado, no net_of_vat(60500)
    assert k.gross_margin_amount == 100000 - 40000  # ventas netas − food neto
    assert k.food_cost_ratio_bps == 4000  # 40000/100000 = 40%


def test_missing_net_food_falls_back_to_global_renetting() -> None:
    # Sin neto per-insumo (filas viejas / construcción directa) cae al re-neteo
    # global — comportamiento previo, paridad hacia atrás.
    k = _kpis(vat_bps=2100, food=60500, food_net=None)
    assert k._net_food_cost == 50000  # net_of_vat(60500, 2100)
