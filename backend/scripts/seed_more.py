"""Add another batch of (profitable) sales to the demo tenant and recalibrate the
advisor's fixed costs to realistic values so the P&L is clearly positive.

Why: the tenant had labor_cost = $30,000,000/month configured (≈2.4× monthly
sales) → the advisor (correctly) reported a big loss. This sets labor/other to a
sane fraction of monthly sales and adds more volume.

    SEED_DSN="postgresql://..." poetry run python scripts/seed_more.py --yes
Without --yes it prints the plan and writes nothing.
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_demo import MENU, RECIPES, TENANT  # noqa: E402

UTC = timezone.utc
CUR = "ARS"
DAYS = 60
TODAY = datetime(2026, 6, 25, tzinfo=UTC)
HOURS = [8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 16, 16, 17, 17, 18, 19, 20]
METHODS = ["CASH"] * 45 + ["CARD"] * 30 + ["MERCADOPAGO"] * 15 + ["TRANSFER"] * 7 + ["QR"] * 3
WEIGHT = {name: w for name, _p, _c, w in MENU}
random.seed(7)


def nid() -> uuid.UUID:
    return uuid.uuid4()


async def main() -> None:
    commit = "--yes" in sys.argv
    conn = await asyncpg.connect(os.environ["SEED_DSN"])
    try:
        waiters = [
            r["id"]
            for r in await conn.fetch(
                "select id from users where tenant_id=$1 and "
                "(email='bravo@gmail.com' or (email like 'mozo%@bravo.demo'))",
                TENANT,
            )
        ]
        tables = [r["id"] for r in await conn.fetch("select id from tables where tenant_id=$1", TENANT)]
        prods = await conn.fetch(
            "select id, name, price_amount, category from products "
            "where tenant_id=$1 and name <> 'aaaaa' and active=true",
            TENANT,
        )
        names = [p["name"] for p in prods]
        weights = [WEIGHT.get(p["name"], 5) for p in prods]
        by_name = {p["name"]: p for p in prods}

        orders_rows, items_rows, pay_rows, fact_rows = [], [], [], []
        day = TODAY - timedelta(days=DAYS)
        while day < TODAY:
            weekend = day.weekday() >= 5
            n = int(45 * (1.6 if weekend else 1.0) * random.uniform(0.85, 1.2))
            for _ in range(n):
                created = day.replace(
                    hour=random.choice(HOURS), minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                oid, table_id, waiter = nid(), random.choice(tables), random.choice(waiters)
                k = random.choices([1, 2, 3, 4, 5], weights=[20, 35, 25, 12, 8])[0]
                chosen = random.choices(names, weights=weights, k=k)
                total, pos = 0, 0
                for cn in dict.fromkeys(chosen):
                    qty = chosen.count(cn)
                    p = by_name[cn]
                    price = p["price_amount"]
                    line = price * qty
                    total += line
                    item_id = nid()
                    items_rows.append((item_id, TENANT, oid, p["id"], cn, price, qty, None, pos, created))
                    fc = round(price * 0.27) * qty if cn in RECIPES else None
                    fact_rows.append((
                        nid(), TENANT, oid, item_id, p["id"], cn, p["category"], qty, price, line,
                        fc, CUR, waiter, table_id, created, created,
                    ))
                    pos += 1
                orders_rows.append((oid, TENANT, table_id, waiter, "PAID", CUR, created))
                pay_rows.append((
                    nid(), TENANT, "INFLOW", total, CUR, random.choice(METHODS), "CONFIRMED",
                    oid, None, None, None, None, created + timedelta(minutes=random.randint(20, 90)),
                ))
            day += timedelta(days=1)

        added_sales = sum(r[9] for r in fact_rows)
        existing_sales = await conn.fetchval(
            "select coalesce(sum(line_amount),0) from sale_facts where tenant_id=$1", TENANT
        )
        total_sales = existing_sales + added_sales
        monthly = round(total_sales / 3)  # ~3 months of history
        labor = round(monthly * 0.32)
        other_fixed = round(monthly * 0.20)

        print("PLAN:")
        print(f"  new orders: {len(orders_rows)}  items: {len(items_rows)}  facts: {len(fact_rows)}")
        print(f"  ventas: existentes ${existing_sales/100:,.0f} + nuevas ${added_sales/100:,.0f} = ${total_sales/100:,.0f}")
        print(f"  advisor_settings -> labor ${labor/100:,.0f}/mes, otros fijos ${other_fixed/100:,.0f}/mes")
        food = await conn.fetchval(
            "select coalesce(sum(food_cost_amount),0) from sale_facts where tenant_id=$1", TENANT
        ) + sum((r[10] or 0) for r in fact_rows)
        net_month = monthly - round(food / 3) - labor - other_fixed
        print(f"  net mensual estimado: ${net_month/100:,.0f}  ({'POSITIVO' if net_month > 0 else 'NEGATIVO'})")

        if not commit:
            print("\nDRY RUN — nothing written. Re-run with --yes to commit.")
            return

        tx = conn.transaction()
        await tx.start()
        try:
            await conn.copy_records_to_table(
                "orders", records=orders_rows,
                columns=["id", "tenant_id", "table_id", "waiter_id", "status", "currency", "created_at"],
            )
            await conn.copy_records_to_table(
                "order_items", records=items_rows,
                columns=["id", "tenant_id", "order_id", "product_id", "name", "unit_price_amount", "quantity", "note", "position", "created_at"],
            )
            await conn.copy_records_to_table(
                "payments", records=pay_rows,
                columns=["id", "tenant_id", "direction", "amount", "currency", "method", "status", "order_id", "category", "counterparty", "description", "external_ref", "created_at"],
            )
            await conn.copy_records_to_table(
                "sale_facts", records=fact_rows,
                columns=["id", "tenant_id", "order_id", "order_item_id", "product_id", "product_name", "category", "quantity", "unit_price_amount", "line_amount", "food_cost_amount", "currency", "waiter_id", "table_id", "occurred_at", "created_at"],
            )
            await conn.execute(
                "update advisor_settings set labor_cost_amount=$2, other_fixed_amount=$3, updated_at=now() "
                "where tenant_id=$1",
                TENANT, labor, other_fixed,
            )
            await tx.commit()
            print("\nCOMMITTED ✅")
        except Exception:
            await tx.rollback()
            raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
