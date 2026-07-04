"""One-off: fix the demo seed where money was loaded in pesos instead of minor
units (×100 too small). Surgically scales ONLY the demo rows (by menu-name and
order linkage), never the pre-existing test rows. Runs in one transaction.

    SEED_DSN="postgresql://..." poetry run python scripts/fix_seed_prices.py
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_demo import MENU, TENANT  # noqa: E402

MENU_NAMES = [m[0] for m in MENU]

# Demo orders = orders that contain at least one item of our seeded menu. This
# excludes the pre-existing test orders (which reference product "aaaaa" or have
# no items).
_DEMO_ORDERS = (
    "select distinct i.order_id from order_items i "
    "where i.tenant_id=$1 and i.product_id in "
    "(select id from products where tenant_id=$1 and name = ANY($2::text[]))"
)


async def main() -> None:
    dsn = os.environ["SEED_DSN"]
    conn = await asyncpg.connect(dsn)
    try:
        before = await conn.fetchval(
            "select coalesce(sum(line_amount),0) from sale_facts where tenant_id=$1", TENANT
        )
        tx = conn.transaction()
        await tx.start()
        try:
            await conn.execute(
                "update products set price_amount=price_amount*100 "
                "where tenant_id=$1 and name = ANY($2::text[])",
                TENANT, MENU_NAMES,
            )
            await conn.execute(
                "update ingredients set unit_cost_amount=unit_cost_amount*100 where tenant_id=$1",
                TENANT,
            )
            await conn.execute(
                f"update order_items set unit_price_amount=unit_price_amount*100 "
                f"where tenant_id=$1 and order_id in ({_DEMO_ORDERS})",
                TENANT, MENU_NAMES,
            )
            await conn.execute(
                f"update sale_facts set unit_price_amount=unit_price_amount*100, "
                f"line_amount=line_amount*100, food_cost_amount=food_cost_amount*100 "
                f"where tenant_id=$1 and order_id in ({_DEMO_ORDERS})",
                TENANT, MENU_NAMES,
            )
            await conn.execute(
                f"update payments set amount=amount*100 "
                f"where tenant_id=$1 and order_id in ({_DEMO_ORDERS})",
                TENANT, MENU_NAMES,
            )
            await conn.execute(
                "update payments set amount=amount*100 "
                "where tenant_id=$1 and direction='OUTFLOW' and order_id is null",
                TENANT,
            )
            await tx.commit()
        except Exception:
            await tx.rollback()
            raise

        after = await conn.fetchval(
            "select coalesce(sum(line_amount),0) from sale_facts where tenant_id=$1", TENANT
        )
        print(f"ventas: ${before/100:,.0f}  ->  ${after/100:,.0f}")
        for r in await conn.fetch(
            "select name, price_amount from products where tenant_id=$1 and name = ANY($2::text[]) "
            "order by name limit 4",
            TENANT, MENU_NAMES,
        ):
            print(f"  {r['name']}: ${r['price_amount']/100:,.2f}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
