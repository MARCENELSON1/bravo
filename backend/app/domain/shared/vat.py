"""VAT (IVA) helper shared across domains. Pure math, integer minor units.

Single source of truth for "back out an IVA-included total to its net" — used by
the advisor KPIs, the food-cost math and every read model that puts sales and
cost on the same (net) basis. Kept here (domain/shared) so nothing imports it
across bounded contexts.
"""

from __future__ import annotations


def net_of_vat(amount: int, rate_bps: int) -> int:
    """Amount net of an IVA-included total: ``total × 10000 / (10000 + rate)``.

    ``rate_bps`` ≤ 0 → identity (no netting / VAT off), so callers stay backward
    compatible when the tenant hasn't loaded an IVA rate.
    """
    if rate_bps <= 0:
        return amount
    return round(amount * 10000 / (10000 + rate_bps))
