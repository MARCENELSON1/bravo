# Implementation Report: Productos v3 — Fase 2B (IVA neto / Solución 1)

## Summary
IVA (VAT) support across the cost/margin engine, opt-in and **off by default**
(`advisor_settings.default_vat_bps = 0` → net == gross → nothing changes live).
The owner loads their IVA rate once; margins/ratios become **net of VAT**, while
prices/sales/ticket stay **gross** (B2 presentation). Per-ingredient precision via
`ingredients.cost_includes_tax` (monotributo suppliers don't get netted).

**Design — "Solución 1 / freeze-both":** both the net-of-VAT **sales** and the
per-ingredient net **food cost** are frozen at projection time (`sale_facts`
`line_net_amount` + `food_cost_net_amount`, and the same two on
`finance_daily_snapshots`). Every aggregate margin read model computes
`net_sales − net_food` by summing the frozen columns — **no read-time re-netting**,
so the two sides can never drift when the VAT rate changes later. A shared
`net_of_vat` lives in `domain/shared/vat.py`; shared SQL column helpers in
`infrastructure/persistence/sale_fact_columns.py`.

## Consistency rule applied everywhere
- **Gross** (displayed): price, sales, ticket, `food_cost_amount` (COGS money),
  RevenueSummary (fully gross, reconciles).
- **Net of IVA**: margin ("te deja"), food-cost ratio, break-even (grossed back
  to gross-sales base), prime cost.
- Productos catalog carries a footnote explaining the convention; the Asesor
  explains it on the IVA field.

## Migrations
- `0023_default_vat` — `advisor_settings.default_vat_bps` (default 0).
- `0024_cost_includes_tax` — `ingredients.cost_includes_tax` (default true).
- `0025_food_cost_net` — frozen net columns on `sale_facts` (nullable) +
  `finance_daily_snapshots` (default 0), **backfilled net = gross** for existing
  rows (correct for the VAT-off history; fixes the snapshot-net-0 case).

## Code review (xhigh, 30 agents) — 12 findings, all resolved
5 correctness + reconciliation issues (stale-net asymmetry on rate change,
Productos net vs gross COGS, snapshot net=0, PurchaseSheet lost-update,
RevenueSummary non-reconciling, break-even net-vs-gross, per-line rounding) and
the cleanups (DRY the COALESCE + VAT lookup, resolve_preparation_costs twice,
import from shared, dead `UTC = UTC`). 2 refuted (round()/float precision).
All fixed and re-reported via ReportFindings.

## Validation
| Level | Status |
|---|---|
| Backend tests | ✅ 416 passed |
| Backend ruff (changed files) | ✅ clean |
| Frontend build | ✅ |
| Frontend lint | ✅ |
| Frontend tests | ✅ 143 passed |
| Migrations (dev) | ✅ up to 0025 applied |

New e2e `test_advisor_aggregate_uses_per_ingredient_net` proves the Asesor
aggregate uses per-ingredient net (monotributo ingredient → 1900 bps, not the
1744 bps a global re-net would give).

## Known limitation (by design, documented)
Changing the IVA rate **after** selling applies going forward; past sales keep
their captured net basis (both sides frozen → internally consistent). A full
retroactive re-net would need an in-place reprojection that preserves dates —
deferred as a future enhancement. Off by default, so nothing is affected until a
tenant opts in.

## Deferred (still 2C/2D of Productos v3)
Unit conversion (2C), price versioning + replacement cost (2D). Nested-prep stock
consumption remains deferred (food cost is exact; stock consumption skips prep
items).
