"""Seed coherent demo data into an EXISTING tenant (Bravo-cafe-bistro).

Additive and tenant-scoped: it never touches other tenants and never deletes.
Everything runs in a single transaction. The DB DSN is read from $SEED_DSN so the
secret is not stored in the file. Run:

    SEED_DSN="postgresql://USER:PASS@HOST:PORT/db" poetry run python scripts/seed_demo.py --yes

Without --yes it prints the plan (row counts) and writes nothing.
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

UTC = timezone.utc
TENANT = uuid.UUID("d3721920-c102-4ae6-b0fd-8aae401f55a0")
OWNER_EMAIL = "bravo@gmail.com"
CUR = "ARS"
DAYS = 90
TODAY = datetime(2026, 6, 25, tzinfo=UTC)

random.seed(42)


def nid() -> uuid.UUID:
    return uuid.uuid4()


# name, price (minor units), category, popularity weight
MENU = [
    ("Café espresso", 2200, "Café", 10),
    ("Café con leche", 3200, "Café", 14),
    ("Cortado", 2400, "Café", 12),
    ("Capuchino", 3800, "Café", 11),
    ("Flat white", 4200, "Café", 7),
    ("Latte", 4000, "Café", 7),
    ("Té / infusión", 2500, "Café", 5),
    ("Submarino", 4500, "Café", 4),
    ("Medialuna", 1200, "Panadería", 13),
    ("Medialunas x3", 3300, "Panadería", 9),
    ("Tostado JyQ", 5900, "Panadería", 9),
    ("Tostado completo", 6900, "Panadería", 6),
    ("Budín del día", 3500, "Panadería", 5),
    ("Brunch Bravo", 10900, "Brunch", 5),
    ("Avocado toast", 7800, "Brunch", 6),
    ("Huevos revueltos", 6800, "Brunch", 5),
    ("Yogur con granola", 5200, "Brunch", 5),
    ("Sándwich de milanesa", 8900, "Platos", 7),
    ("Ensalada César", 7900, "Platos", 5),
    ("Tarta del día", 6900, "Platos", 5),
    ("Bowl veggie", 8200, "Platos", 4),
    ("Cheesecake", 5800, "Postres", 6),
    ("Brownie con helado", 6200, "Postres", 6),
    ("Alfajor de maicena", 1800, "Postres", 7),
    ("Limonada", 4200, "Bebidas", 6),
    ("Agua mineral", 2200, "Bebidas", 6),
    ("Jugo de naranja", 4500, "Bebidas", 6),
    ("Gaseosa", 3000, "Bebidas", 7),
]

# name, unit, unit_cost (minor), stock_qty, min_qty
INGREDIENTS = [
    ("Café en grano", "dosis", 550, 4000, 500),
    ("Leche", "porción", 350, 3000, 400),
    ("Medialuna (cruda)", "unidad", 420, 1500, 200),
    ("Pan", "unidad", 380, 1200, 150),
    ("Jamón", "porción", 850, 800, 120),
    ("Queso", "porción", 780, 900, 120),
    ("Huevos", "unidad", 320, 2000, 240),
    ("Palta", "porción", 1100, 400, 60),
    ("Yogur", "porción", 900, 300, 50),
    ("Granola", "porción", 700, 350, 50),
    ("Verduras", "porción", 600, 600, 80),
    ("Carne (milanesa)", "porción", 2600, 250, 40),
    ("Azúcar", "porción", 90, 5000, 500),
]

RECIPES = {
    "Café espresso": [("Café en grano", 1)],
    "Café con leche": [("Café en grano", 1), ("Leche", 1)],
    "Cortado": [("Café en grano", 1)],
    "Capuchino": [("Café en grano", 1), ("Leche", 1)],
    "Flat white": [("Café en grano", 1), ("Leche", 1)],
    "Latte": [("Café en grano", 1), ("Leche", 1)],
    "Submarino": [("Leche", 1)],
    "Medialuna": [("Medialuna (cruda)", 1)],
    "Medialunas x3": [("Medialuna (cruda)", 3)],
    "Tostado JyQ": [("Pan", 2), ("Jamón", 1), ("Queso", 1)],
    "Tostado completo": [("Pan", 2), ("Jamón", 1), ("Queso", 1), ("Huevos", 1)],
    "Budín del día": [("Huevos", 1), ("Azúcar", 1)],
    "Brunch Bravo": [("Pan", 2), ("Huevos", 2), ("Palta", 1), ("Queso", 1)],
    "Avocado toast": [("Pan", 2), ("Palta", 1)],
    "Huevos revueltos": [("Huevos", 3), ("Pan", 1)],
    "Yogur con granola": [("Yogur", 1), ("Granola", 1)],
    "Sándwich de milanesa": [("Pan", 2), ("Carne (milanesa)", 1)],
    "Ensalada César": [("Verduras", 2), ("Queso", 1)],
    "Tarta del día": [("Huevos", 2), ("Queso", 1), ("Verduras", 1)],
    "Bowl veggie": [("Verduras", 2), ("Palta", 1)],
}

STAFF = [
    ("mozo.ana@bravo.demo", "WAITER"),
    ("mozo.bruno@bravo.demo", "WAITER"),
    ("cocina@bravo.demo", "KITCHEN"),
    ("caja@bravo.demo", "CASHIER"),
]

NEW_TABLES = [
    "Ventana 1", "Ventana 2", "Barra 1", "Barra 2", "Vereda 1", "Vereda 2",
    "Salón 1", "Salón 2", "Salón 3", "Salón 4", "Reservado", "Terraza",
]

# Open 8–20, weighted toward breakfast and lunch peaks.
HOURS = [8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 16, 16, 17, 17, 18, 19, 20]
METHODS = ["CASH"] * 45 + ["CARD"] * 30 + ["MERCADOPAGO"] * 15 + ["TRANSFER"] * 7 + ["QR"] * 3
LIVE_STATES = [
    "OPEN", "SENT", "SENT", "PREPARING", "PREPARING", "READY",
    "SERVED", "SERVED", "SENT", "PREPARING", "READY", "OPEN",
]


async def main() -> None:
    commit = "--yes" in sys.argv
    dsn = os.environ.get("SEED_DSN")
    if not dsn:
        print("ERROR: set $SEED_DSN")
        sys.exit(1)

    conn = await asyncpg.connect(dsn)
    try:
        owner_id = await conn.fetchval(
            "select id from users where tenant_id=$1 and email=$2", TENANT, OWNER_EMAIL
        )
        if owner_id is None:
            print("ERROR: owner not found")
            sys.exit(1)

        # --- build the data in memory ---
        prod: dict[str, tuple[uuid.UUID, int, str]] = {}
        for name, price, cat, _w in MENU:
            prod[name] = (nid(), price, cat)

        ing: dict[str, tuple[uuid.UUID, int]] = {}
        for name, _u, cost, _s, _m in INGREDIENTS:
            ing[name] = (nid(), cost)

        food_cost: dict[str, int] = {}
        for pname, recipe in RECIPES.items():
            food_cost[pname] = sum(qty * ing[i][1] for i, qty in recipe)

        staff: dict[str, uuid.UUID] = {email: nid() for email, _r in STAFF}
        waiters = [owner_id, staff["mozo.ana@bravo.demo"], staff["mozo.bruno@bravo.demo"]]

        existing = await conn.fetch("select id, number from tables where tenant_id=$1", TENANT)
        table_ids = [r["id"] for r in existing]
        max_num = max((r["number"] for r in existing), default=0)
        new_tables = [(nid(), max_num + 1 + i, tn) for i, tn in enumerate(NEW_TABLES)]
        table_ids += [t[0] for t in new_tables]

        menu_names = [m[0] for m in MENU]
        weights = [m[3] for m in MENU]

        orders_rows, items_rows, pay_rows, fact_rows = [], [], [], []

        def add_order(oid, table_id, waiter, status, created, paid):
            k = random.choices([1, 2, 3, 4, 5], weights=[20, 35, 25, 12, 8])[0]
            chosen = random.choices(menu_names, weights=weights, k=k)
            total, pos = 0, 0
            for cn in dict.fromkeys(chosen):  # distinct, preserve order
                qty = chosen.count(cn)
                pid, price, cat = prod[cn]
                line = price * qty
                total += line
                item_id = nid()
                items_rows.append(
                    (item_id, TENANT, oid, pid, cn, price, qty, None, pos, created)
                )
                if paid:
                    fc = food_cost.get(cn)
                    fact_rows.append((
                        nid(), TENANT, oid, item_id, pid, cn, cat, qty, price, line,
                        fc * qty if fc is not None else None, CUR, waiter, table_id,
                        created, created,
                    ))
                pos += 1
            orders_rows.append((oid, TENANT, table_id, waiter, status, CUR, created))
            return total

        # historical PAID orders over the period
        day = TODAY - timedelta(days=DAYS)
        while day < TODAY:
            weekend = day.weekday() >= 5
            n = int(38 * (1.6 if weekend else 1.0) * random.uniform(0.8, 1.2))
            for _ in range(n):
                created = day.replace(
                    hour=random.choice(HOURS), minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                oid, table_id, waiter = nid(), random.choice(table_ids), random.choice(waiters)
                total = add_order(oid, table_id, waiter, "PAID", created, paid=True)
                pay_rows.append((
                    nid(), TENANT, "INFLOW", total, CUR, random.choice(METHODS), "CONFIRMED",
                    oid, None, None, None, None, created + timedelta(minutes=random.randint(20, 90)),
                ))
            day += timedelta(days=1)

        # live orders today (floor occupied + KDS active); not PAID → no payment/facts
        live_tables = random.sample(table_ids, min(len(LIVE_STATES), len(table_ids)))
        for i, st in enumerate(LIVE_STATES):
            created = TODAY.replace(hour=13, minute=0) - timedelta(minutes=random.randint(3, 55))
            add_order(nid(), live_tables[i % len(live_tables)], random.choice(waiters), st, created, paid=False)

        # expenses (OUTFLOW): weekly supplies + monthly rent/payroll/utilities
        d = TODAY - timedelta(days=DAYS)
        while d < TODAY:
            pay_rows.append((
                nid(), TENANT, "OUTFLOW", random.randint(150000, 420000), CUR, "TRANSFER",
                "CONFIRMED", None, "Proveedores", "Distribuidora", "Compra de insumos", None,
                d.replace(hour=10) + timedelta(days=1),
            ))
            d += timedelta(days=7)
        for m_off in range(3):
            md = (TODAY.replace(day=1) - timedelta(days=31 * m_off)).replace(day=5, hour=9)
            for amt, cat, who, desc, meth in [
                (random.randint(1100000, 1400000), "Sueldos", "Personal", "Sueldos del mes", "TRANSFER"),
                (random.randint(750000, 850000), "Alquiler", "Inmobiliaria", "Alquiler", "TRANSFER"),
                (random.randint(150000, 210000), "Servicios", "Servicios", "Luz/gas/internet", "CARD"),
            ]:
                pay_rows.append((
                    nid(), TENANT, "OUTFLOW", amt, CUR, meth, "CONFIRMED", None, cat, who, desc, None, md,
                ))

        plan = {
            "staff_users": len(STAFF), "products": len(MENU), "ingredients": len(INGREDIENTS),
            "recipes": len(RECIPES), "new_tables": len(NEW_TABLES), "orders": len(orders_rows),
            "order_items": len(items_rows), "payments": len(pay_rows), "sale_facts": len(fact_rows),
        }
        print("PLAN (additive, tenant Bravo-cafe-bistro):")
        for k, v in plan.items():
            print(f"  {k}: {v}")

        if not commit:
            print("\nDRY RUN — nothing written. Re-run with --yes to commit.")
            return

        tx = conn.transaction()
        await tx.start()
        try:
            for email, role in STAFF:
                await conn.execute(
                    "insert into users(id,tenant_id,email,password_hash,role,email_verified,active,failed_attempts)"
                    " values($1,$2,$3,NULL,$4,true,true,0)",
                    staff[email], TENANT, email, role,
                )
            for name, price, cat, _w in MENU:
                pid, _p, _c = prod[name]
                await conn.execute(
                    "insert into products(id,tenant_id,name,price_amount,price_currency,category,active)"
                    " values($1,$2,$3,$4,$5,$6,true)",
                    pid, TENANT, name, price, CUR, cat,
                )
            for name, unit, cost, stock, minq in INGREDIENTS:
                await conn.execute(
                    "insert into ingredients(id,tenant_id,name,unit,stock_qty,min_qty,unit_cost_amount,unit_cost_currency,active)"
                    " values($1,$2,$3,$4,$5,$6,$7,$8,true)",
                    ing[name][0], TENANT, name, unit, stock, minq, cost, CUR,
                )
            for pname, recipe in RECIPES.items():
                pid = prod[pname][0]
                await conn.execute(
                    "insert into recipes(product_id,tenant_id) values($1,$2)", pid, TENANT
                )
                for iname, qty in recipe:
                    await conn.execute(
                        "insert into recipe_items(id,tenant_id,product_id,ingredient_id,qty) values($1,$2,$3,$4,$5)",
                        nid(), TENANT, pid, ing[iname][0], qty,
                    )
            for tid, number, tname in new_tables:
                await conn.execute(
                    "insert into tables(id,tenant_id,number,name,active) values($1,$2,$3,$4,true)",
                    tid, TENANT, number, tname,
                )

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
            await tx.commit()
            print("\nCOMMITTED ✅")
        except Exception:
            await tx.rollback()
            raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
