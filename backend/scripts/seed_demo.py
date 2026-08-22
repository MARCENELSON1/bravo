"""Siembra datos de demo coherentes en un tenant existente.

Reemplaza al seeder original, que tenía dos problemas: la fecha estaba clavada
(``TODAY = datetime(2026, 6, 25)``), así que los datos envejecían y el Home —que
mira "hoy"— quedaba en cero; y solo llenaba una parte del modelo, por lo que
todas las features posteriores (comisiones, ARCA, recetas madre, stock,
reservas, snapshots) se veían vacías.

Este script:
  * genera todo **relativo a hoy**, así se puede volver a correr cuando se quiera;
  * **borra y resiembra** el tenant (idempotente), estrictamente acotado por
    ``tenant_id`` — nunca toca otros tenants ni los usuarios existentes;
  * cubre el modelo completo, incluidas las columnas nuevas que quedaban en NULL;
  * calibra los números contra la realidad del rubro, porque el Asesor **calcula
    sobre estos datos**: sembrar cifras arbitrarias produce diagnósticos absurdos.

Perfil simulado: bistró de barrio, 40 cubiertos, almuerzo y cena, ticket medio
cercano a $28.000 por mesa.

Tres problemas plantados a propósito, para que el Asesor tenga qué detectar
(un local sin problemas no genera ni una recomendación útil):
  1. un plato con el food cost muy por encima del objetivo;
  2. un insumo que subió fuerte y cuyo aumento no se trasladó al precio;
  3. merma alta en un insumo caro.

Uso:
    SEED_DSN="postgresql://USER:PASS@HOST:PORT/db" \\
      poetry run python scripts/seed_demo.py --tenant bravo --yes

Sin ``--yes`` imprime el plan y no escribe nada.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg

CUR = "ARS"
DAYS = 120
# El dominio guarda TODAS las cantidades de inventario en milésimas de la unidad
# base: qty de movimientos y de recetas, stock_qty, min_qty y yield_qty. Las
# constantes de este archivo están en unidades legibles (400 = 400 g) y se
# convierten al escribir. Sin esto la merma se lee como 0 y el stock como polvo.
MIL = 1000
random.seed(7)

# Se fija una sola vez por corrida: todo el dataset cuelga de acá.
NOW = datetime.now(UTC)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)


def nid() -> uuid.UUID:
    return uuid.uuid4()


# ── Carta ────────────────────────────────────────────────────────────────────
# (nombre, precio en centavos, categoría, peso de popularidad, estación)
MENU = [
    # Entradas
    ("Provoleta al horno",        620000, "Entradas",   7,  "KITCHEN"),
    ("Empanadas de carne x3",     540000, "Entradas",   9,  "KITCHEN"),
    ("Rabas a la provenzal",      890000, "Entradas",   5,  "KITCHEN"),
    ("Burrata con tomates",       750000, "Entradas",   5,  "KITCHEN"),
    # Principales
    ("Ojo de bife 400g",         1450000, "Principales", 9, "KITCHEN"),
    ("Bife de chorizo",          1320000, "Principales", 8, "KITCHEN"),
    ("Milanesa napolitana",      1080000, "Principales", 12, "KITCHEN"),
    ("Salmón grillado",          1380000, "Principales", 6, "KITCHEN"),
    ("Pollo al verdeo",           980000, "Principales", 7, "KITCHEN"),
    ("Risotto de hongos",         960000, "Principales", 5, "KITCHEN"),
    ("Sorrentinos de calabaza",   980000, "Principales", 8, "KITCHEN"),
    ("Ñoquis con estofado",       890000, "Principales", 6, "KITCHEN"),
    ("Langostinos al ajillo",    1520000, "Principales", 4, "KITCHEN"),
    ("Ensalada del bistró",       720000, "Principales", 5, "KITCHEN"),
    # Guarniciones
    ("Papas rústicas",            420000, "Guarniciones", 9, "KITCHEN"),
    ("Puré de calabaza",          390000, "Guarniciones", 5, "KITCHEN"),
    # Postres
    ("Flan casero",               450000, "Postres",     7, "KITCHEN"),
    ("Tiramisú",                  520000, "Postres",     6, "KITCHEN"),
    ("Volcán de chocolate",       550000, "Postres",     6, "KITCHEN"),
    # Barra — bebidas con alcohol
    ("Copa de Malbec",            450000, "Vinos",      11, "BAR"),
    ("Botella Malbec reserva",   1600000, "Vinos",       6, "BAR"),
    ("Copa de Torrontés",         420000, "Vinos",       5, "BAR"),
    ("Cerveza artesanal pinta",   380000, "Cervezas",   10, "BAR"),
    ("Gin tonic",                 620000, "Cócteles",    6, "BAR"),
    ("Aperol spritz",             650000, "Cócteles",    6, "BAR"),
    # Barra — sin alcohol
    ("Agua mineral",              220000, "Bebidas",    10, "BAR"),
    ("Gaseosa línea Coca",        280000, "Bebidas",     9, "BAR"),
    ("Limonada de la casa",       350000, "Bebidas",     6, "BAR"),
    ("Café espresso",             250000, "Café",        8, "BAR"),
    ("Cortado",                   270000, "Café",        6, "BAR"),
]

# (nombre, unidad de compra, costo unitario en centavos, stock, mínimo,
#  rendimiento %, el costo incluye IVA, unidad de receta)
INGREDIENTS = [
    ("Ojo de bife",        "kg",      1850000, 45,  15, 82,  True,  "g"),
    ("Bife de chorizo",    "kg",      1620000, 38,  12, 85,  True,  "g"),
    ("Nalga para milanesa", "kg",     1280000, 52,  18, 88,  True,  "g"),
    ("Salmón fresco",      "kg",      2950000, 14,   6, 78,  True,  "g"),
    ("Langostinos",        "kg",      3200000, 11,   5, 70,  True,  "g"),
    ("Pechuga de pollo",   "kg",       890000, 34,  12, 90,  True,  "g"),
    ("Harina 000",         "kg",        95000, 60,  20, 100, False, "g"),
    ("Huevos",             "docena",   380000, 28,  10, 100, False, "unidad"),
    ("Muzzarella",         "kg",      1150000, 26,  10, 95,  True,  "g"),
    ("Provolone",          "kg",      1680000,  9,   4, 95,  True,  "g"),
    ("Burrata",            "unidad",   620000, 16,   8, 100, True,  "unidad"),
    ("Papa",               "kg",       125000, 85,  30, 80,  False, "g"),
    ("Calabaza",           "kg",       145000, 32,  12, 72,  False, "g"),
    ("Tomate",             "kg",       230000, 24,  10, 88,  False, "g"),
    ("Verdeo y hierbas",   "kg",       310000, 12,   5, 85,  False, "g"),
    ("Hongos secos",       "kg",      2400000,  6,   3, 100, True,  "g"),
    ("Arroz carnaroli",    "kg",       420000, 18,   8, 100, False, "g"),
    ("Crema de leche",     "litro",    310000, 22,   8, 100, True,  "ml"),
    ("Manteca",            "kg",       780000, 14,   6, 100, True,  "g"),
    ("Chocolate cobertura", "kg",     1450000,  8,   4, 100, True,  "g"),
    ("Dulce de leche",     "kg",       520000, 11,   5, 100, True,  "g"),
    ("Café en grano",      "kg",      1250000, 15,   6, 100, True,  "g"),
    ("Aceite de oliva",    "litro",    680000, 13,   5, 100, True,  "ml"),
    ("Calamar",            "kg",      1450000,  9,   4, 75,  True,  "g"),
]

# Preparaciones base (recetas madre): nombre → (rendimiento, [(insumo, cantidad)])
PREPARATIONS = {
    "Salsa napolitana":  (2000, [("Tomate", 1500), ("Aceite de oliva", 120),
                                 ("Verdeo y hierbas", 80)]),
    "Masa de empanada":  (40,   [("Harina 000", 1200), ("Manteca", 260), ("Huevos", 2)]),
    "Puré base":         (1500, [("Calabaza", 1800), ("Crema de leche", 200), ("Manteca", 80)]),
    "Fondo de hongos":   (1000, [("Hongos secos", 90), ("Crema de leche", 350), ("Manteca", 60)]),
}

# Recetas: plato → [(tipo, nombre, cantidad)] donde tipo es "i" (insumo) o "p" (preparación)
RECIPES: dict[str, list[tuple[str, str, int]]] = {
    "Provoleta al horno":      [("i", "Provolone", 180), ("i", "Aceite de oliva", 15)],
    "Empanadas de carne x3":   [("p", "Masa de empanada", 3), ("i", "Nalga para milanesa", 150)],
    "Rabas a la provenzal":    [("i", "Calamar", 220), ("i", "Aceite de oliva", 30)],
    "Burrata con tomates":     [("i", "Burrata", 1), ("i", "Tomate", 180)],
    # Problema 1: food cost muy por encima del objetivo — la porción es grande
    # y el precio quedó viejo.
    "Ojo de bife 400g":        [("i", "Ojo de bife", 400), ("i", "Papa", 200)],
    "Bife de chorizo":         [("i", "Bife de chorizo", 320), ("i", "Papa", 180)],
    "Milanesa napolitana":     [("i", "Nalga para milanesa", 260), ("i", "Huevos", 1),
                                ("i", "Harina 000", 60), ("i", "Muzzarella", 90),
                                ("p", "Salsa napolitana", 120)],
    "Salmón grillado":         [("i", "Salmón fresco", 220), ("p", "Puré base", 180)],
    "Pollo al verdeo":         [("i", "Pechuga de pollo", 280), ("i", "Verdeo y hierbas", 40),
                                ("i", "Crema de leche", 80)],
    "Risotto de hongos":       [("i", "Arroz carnaroli", 110), ("p", "Fondo de hongos", 150)],
    "Sorrentinos de calabaza": [("i", "Harina 000", 140), ("i", "Huevos", 1),
                                ("p", "Puré base", 120)],
    "Ñoquis con estofado":     [("i", "Papa", 300), ("i", "Harina 000", 90),
                                ("i", "Nalga para milanesa", 120)],
    # Problema 3: merma alta — los langostinos se descartan seguido.
    "Langostinos al ajillo":   [("i", "Langostinos", 165), ("i", "Aceite de oliva", 40)],
    "Ensalada del bistró":     [("i", "Tomate", 150), ("i", "Verdeo y hierbas", 60),
                                ("i", "Muzzarella", 60)],
    "Papas rústicas":          [("i", "Papa", 280), ("i", "Aceite de oliva", 20)],
    "Puré de calabaza":        [("p", "Puré base", 220)],
    "Flan casero":             [("i", "Huevos", 2), ("i", "Dulce de leche", 60)],
    "Tiramisú":                [("i", "Café en grano", 12), ("i", "Crema de leche", 120),
                                ("i", "Chocolate cobertura", 30)],
    "Volcán de chocolate":     [("i", "Chocolate cobertura", 80), ("i", "Manteca", 40),
                                ("i", "Huevos", 1)],
    "Café espresso":           [("i", "Café en grano", 9)],
    "Cortado":                 [("i", "Café en grano", 9), ("i", "Crema de leche", 30)],
}

SUPPLIERS = [
    ("Frigorífico San Cayetano", "Ventas: 11-4455-8890"),
    ("Distribuidora La Rioja",   "pedidos@larioja.com.ar"),
    ("Verdulería Del Mercado",   "11-6677-2211"),
    ("Pescadería Mar del Sur",   "ventas@mardelsur.com.ar"),
    ("Bodega Alto Valle",        "comercial@altovalle.com.ar"),
]

STAFF = [
    ("mozo.ana@bravo.demo",     "WAITER",  "Ana Ferreyra"),
    ("mozo.bruno@bravo.demo",   "WAITER",  "Bruno Sosa"),
    ("mozo.caro@bravo.demo",    "WAITER",  "Carolina Ruiz"),
    ("cocina@bravo.demo",       "KITCHEN", "Diego Paz"),
    ("barra@bravo.demo",        "BAR",     "Lucía Medina"),
    ("caja@bravo.demo",         "CASHIER", "Martín Godoy"),
]

TABLE_NAMES = [
    "Salón 1", "Salón 2", "Salón 3", "Salón 4", "Salón 5", "Salón 6",
    "Ventana 1", "Ventana 2", "Ventana 3", "Barra 1", "Barra 2",
    "Vereda 1", "Vereda 2", "Vereda 3", "Reservado", "Terraza",
]

# Almuerzo 12–15, cena 20–24. Un bistró concentra la facturación en la cena.
LUNCH_HOURS = [12, 12, 13, 13, 13, 14, 14, 15]
DINNER_HOURS = [20, 20, 21, 21, 21, 22, 22, 22, 23, 23]
METHODS = ["CASH"] * 22 + ["CARD"] * 38 + ["MERCADOPAGO"] * 24 + ["TRANSFER"] * 6 + ["QR"] * 10
FEE_BPS = {"CARD": 350, "MERCADOPAGO": 299, "QR": 80, "CASH": 0, "TRANSFER": 0}
LIVE_STATES = ["OPEN", "SENT", "SENT", "PREPARING", "PREPARING", "READY", "SERVED", "SENT"]

# Orden de borrado: hijos antes que padres.
WIPE_ORDER = [
    "sale_facts", "invoices", "payments", "cash_counts", "cash_sessions",
    "order_items", "orders", "stock_movements", "recipe_items", "recipes",
    "preparation_items", "preparations", "product_price_changes", "products",
    "ingredients", "suppliers", "tip_payouts", "reservations", "tables",
    "finance_daily_snapshots", "advisor_diagnostics", "payment_fee_rates",
    "payment_credentials", "tax_credentials", "shifts",
]


def money(minor: int) -> str:
    return f"${minor / 100:,.0f}".replace(",", ".")


async def main() -> None:
    ap = argparse.ArgumentParser(description="Siembra datos de demo en un tenant.")
    ap.add_argument("--tenant", default="bravo", help="slug del tenant (default: bravo)")
    ap.add_argument("--yes", action="store_true", help="escribir (sin esto es una simulación)")
    args = ap.parse_args()

    dsn = os.environ.get("SEED_DSN")
    if not dsn:
        print("ERROR: falta $SEED_DSN")
        sys.exit(1)

    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow("select id, name from tenants where slug=$1", args.tenant)
        if row is None:
            print(f"ERROR: no existe el tenant '{args.tenant}'")
            sys.exit(1)
        tenant, tenant_name = row["id"], row["name"]

        owner = await conn.fetchrow(
            "select id, email from users where tenant_id=$1 and role='OWNER'"
            " order by created_at limit 1",
            tenant,
        )
        if owner is None:
            print("ERROR: el tenant no tiene OWNER")
            sys.exit(1)

        # El personal se resuelve contra la base ANTES de armar nada: si ya existe
        # por email hay que reusar su id, o los fichajes y las propinas apuntarían
        # a usuarios inexistentes.
        staff_ids: dict[str, uuid.UUID] = {}
        for email, _role, _name in STAFF:
            found = await conn.fetchval(
                "select id from users where tenant_id=$1 and email=$2", tenant, email)
            staff_ids[email] = found or nid()

        # ── ids en memoria ────────────────────────────────────────────────
        prod = {name: (nid(), price, cat, station) for name, price, cat, _w, station in MENU}
        ESCALA = 1.35  # nivel de mercado: bistró de gama alta (principal ~$23.000)
        ing = {name: (nid(), int(cost * ESCALA), yld, unit)
               for name, _u, cost, _s, _m, yld, _t, unit in INGREDIENTS}
        prep = {name: (nid(), yield_qty) for name, (yield_qty, _items) in PREPARATIONS.items()}
        supp = {name: nid() for name, _c in SUPPLIERS}
        tables = [(nid(), i + 1, tn) for i, tn in enumerate(TABLE_NAMES)]
        table_ids = [t[0] for t in tables]

        # Cuántas unidades de receta entran en una unidad de compra. Sin esto un
        # huevo costaría lo que la docena y el food cost se va a las nubes.
        PER_PURCHASE = {("kg", "g"): 1000, ("litro", "ml"): 1000, ("docena", "unidad"): 12}
        unit_of = {name: unit for name, unit, *_ in INGREDIENTS}

        def cost_por_unidad_receta(iname: str) -> float:
            unit_cost, recipe_unit = ing[iname][1], ing[iname][3]
            factor = PER_PURCHASE.get((unit_of[iname], recipe_unit), 1)
            return unit_cost / factor

        # ── costo de cada preparación (por unidad de rendimiento) ─────────
        prep_unit_cost: dict[str, float] = {}
        for pname, (yield_qty, items) in PREPARATIONS.items():
            total = sum(cost_por_unidad_receta(i) * qty for i, qty in items)
            prep_unit_cost[pname] = total / yield_qty

        # ── food cost de cada plato ──────────────────────────────────────
        def line_cost(kind: str, name: str, qty: int) -> float:
            if kind == "p":
                return prep_unit_cost[name] * qty
            base = cost_por_unidad_receta(name) * qty
            return base / (ing[name][2] / 100)  # la merma encarece la porción

        food_cost = {p: int(sum(line_cost(k, n, q) for k, n, q in r)) for p, r in RECIPES.items()}

        # El precio se DERIVA del costo, no se fija a mano: así el food cost cierra
        # por construcción en vez de por casualidad. Los platos con problema
        # plantado se dejan con un ratio malo a propósito, que es lo que el Asesor
        # tiene que detectar.
        TARGET = {"Entradas": .31, "Principales": .32, "Guarniciones": .27,
                  "Postres": .24, "Vinos": .30, "Cervezas": .28, "Cócteles": .22,
                  "Bebidas": .20, "Café": .18}
        PROBLEMA = {"Ojo de bife 400g": .44, "Langostinos al ajillo": .41}

        # Piso por categoría: el costo manda hacia arriba, pero nunca hacia abajo
        # de lo que la carta puede pedir. Así los platos baratos de producir
        # quedan con más margen, que es exactamente como se arma una carta real.
        # Pisos altos a propósito: en una carta real no conviven un principal de
        # $23.000 con otro de $7.000, aunque el segundo sea barato de producir.
        PISO = {"Entradas": 900000, "Principales": 1650000, "Guarniciones": 550000,
                "Postres": 700000, "Café": 350000}

        def precio_lindo(v: float) -> int:
            """Redondea a los $500 más cercanos, como haría cualquier carta."""
            return int(round(v / 50000) * 50000)

        for name, (pid, price, cat, station) in list(prod.items()):
            fc = food_cost.get(name)
            if fc is None:      # bebidas sin receta: se escalan igual que la carta
                prod[name] = (pid, precio_lindo(price * ESCALA), cat, station)
                continue
            ratio = PROBLEMA.get(name, TARGET.get(cat, .30))
            prod[name] = (pid, max(precio_lindo(fc / ratio), PISO.get(cat, 200000)),
                          cat, station)

        # ── órdenes históricas ───────────────────────────────────────────
        waiters = [staff_ids["mozo.ana@bravo.demo"], staff_ids["mozo.bruno@bravo.demo"],
                   staff_ids["mozo.caro@bravo.demo"]]

        orders_rows, items_rows, pay_rows, fact_rows, inv_rows = [], [], [], [], []
        stock_rows: list[tuple] = []

        def add_order(oid, table_id, waiter, status, created, paid: bool) -> int:
            """Una mesa de bistró: platos principales + bebida + a veces entrada y postre."""
            n_main = random.choices([1, 2, 3, 4], weights=[30, 45, 18, 7])[0]
            picks: list[str] = []
            mains = [m for m in MENU if m[2] in ("Principales",)]
            picks += [random.choices([m[0] for m in mains], weights=[m[3] for m in mains])[0]
                      for _ in range(n_main)]
            drinks = [m for m in MENU if m[4] == "BAR"]
            picks += [random.choices([m[0] for m in drinks], weights=[m[3] for m in drinks])[0]
                      for _ in range(max(1, n_main - random.randint(0, 1)))]
            if random.random() < 0.42:
                ent = [m for m in MENU if m[2] == "Entradas"]
                picks.append(random.choices([m[0] for m in ent], weights=[m[3] for m in ent])[0])
            if random.random() < 0.33:
                pos_ = [m for m in MENU if m[2] == "Postres"]
                picks.append(random.choices([m[0] for m in pos_], weights=[m[3] for m in pos_])[0])
            if random.random() < 0.30:
                gua = [m for m in MENU if m[2] == "Guarniciones"]
                picks.append(random.choices([m[0] for m in gua], weights=[m[3] for m in gua])[0])

            total, pos = 0, 0
            for cn in dict.fromkeys(picks):
                qty = picks.count(cn)
                pid, price, cat, station = prod[cn]
                line = price * qty
                total += line
                item_id = nid()
                item_status = "SERVED" if paid else random.choice(["SENT", "PREPARING", "READY"])
                items_rows.append((item_id, tenant, oid, pid, cn, price, qty, None, pos,
                                   created, item_status, station,
                                   created + timedelta(minutes=2) if paid else created,
                                   created + timedelta(minutes=14) if paid else None))
                if paid:
                    fc = food_cost.get(cn)
                    fact_rows.append((nid(), tenant, oid, item_id, pid, cn, cat, qty, price, line,
                                      fc * qty if fc is not None else None, CUR, waiter, table_id,
                                      created, created))
                    # consumo de stock por receta
                    for kind, iname, iqty in RECIPES.get(cn, []):
                        if kind == "i":
                            stock_rows.append((nid(), tenant, ing[iname][0], "OUT", "SALE",
                                               iqty * qty * MIL, oid, None, None, None,
                                               created))
                pos += 1
            orders_rows.append((oid, tenant, table_id, waiter, status, CUR, created))
            return total

        day = TODAY - timedelta(days=DAYS)
        while day <= TODAY:
            weekend = day.weekday() >= 4  # viernes a domingo
            base = 34 if weekend else 21
            n = int(base * random.uniform(0.85, 1.15))
            for _ in range(n):
                hours = LUNCH_HOURS if random.random() < 0.38 else DINNER_HOURS
                created = day.replace(hour=random.choice(hours),
                                      minute=random.randint(0, 59), second=random.randint(0, 59))
                if created > NOW:
                    continue
                oid, table_id = nid(), random.choice(table_ids)
                waiter = random.choice(waiters)
                total = add_order(oid, table_id, waiter, "PAID", created, paid=True)
                method = random.choice(METHODS)
                fee = round(total * FEE_BPS[method] / 10000)
                tip = round(total * random.choice([0, 0, 0, 0.05, 0.10])) if method != "CASH" else 0
                paid_at = created + timedelta(minutes=random.randint(45, 110))
                pay_rows.append((nid(), tenant, "INFLOW", total, CUR, method, "CONFIRMED", oid,
                                 None, None, None, None, paid_at, tip, None, fee, total - fee))
                # ~35% de los cobros emiten comprobante
                if random.random() < 0.35:
                    neto = round(total / 1.21)
                    inv_rows.append((nid(), tenant, "FACTURA_B", 1, len(inv_rows) + 1,
                                     "CONSUMIDOR_FINAL", "0", "PRODUCTOS", neto, total - neto,
                                     total, CUR, "[]", "AUTHORIZED",
                                     str(random.randint(70000000000000, 79999999999999)),
                                     (paid_at + timedelta(days=10)).date(), None, oid,
                                     paid_at, paid_at))
            day += timedelta(days=1)

        # ── mesas vivas ahora (plano de salón + KDS + barra con trabajo) ──
        live_tables = random.sample(table_ids, min(len(LIVE_STATES), len(table_ids)))
        for i, st in enumerate(LIVE_STATES):
            created = NOW - timedelta(minutes=random.randint(4, 70))
            add_order(nid(), live_tables[i], random.choice(waiters), st, created, paid=False)

        # ── compras de insumos (stock IN) + el salto de precio del problema 2 ──
        d = TODAY - timedelta(days=DAYS)
        while d < TODAY:
            for iname in random.sample(list(ing), 6):
                iid, cost, _y, _u = ing[iname]
                # Problema 2: el ojo de bife saltó 34% hace 3 semanas y el precio
                # del plato nunca se actualizó.
                bump = 1.34 if (iname == "Ojo de bife" and d > TODAY - timedelta(days=21)) else 1.0
                stock_rows.append((nid(), tenant, iid, "IN", "PURCHASE",
                                   random.randint(8, 30) * MIL, None, int(cost * bump), CUR,
                                   "Compra semanal", d.replace(hour=9)))
            d += timedelta(days=7)

        # Problema 3: merma alta y recurrente en langostinos. La merma DEBE llevar
        # costo unitario o el sistema no puede valorizarla y el KPI muestra 0%.
        d = TODAY - timedelta(days=60)
        while d < TODAY:
            stock_rows.append((nid(), tenant, ing["Langostinos"][0], "OUT", "WASTE",
                               random.randint(2, 5) * MIL, None, ing["Langostinos"][1], CUR,
                               "Descarte por cadena de frío", d.replace(hour=23)))
            d += timedelta(days=random.randint(4, 8))
        # Merma de fondo en otros insumos: un local real descarta un poco de todo.
        d = TODAY - timedelta(days=DAYS)
        while d < TODAY:
            for iname in random.sample(["Tomate", "Verdeo y hierbas", "Papa", "Burrata",
                                        "Salmón fresco", "Crema de leche"], 2):
                stock_rows.append((nid(), tenant, ing[iname][0], "OUT", "WASTE",
                                   random.randint(1, 4) * MIL, None, ing[iname][1], CUR,
                                   "Merma de servicio", d.replace(hour=23, minute=30)))
            d += timedelta(days=random.randint(2, 4))

        # ── egresos ──────────────────────────────────────────────────────
        d = TODAY - timedelta(days=DAYS)
        while d < TODAY:
            for cat, who, lo, hi in [
                ("Proveedores", "Frigorífico San Cayetano", 180000000, 320000000),
                ("Proveedores", "Verdulería Del Mercado", 42000000, 78000000),
            ]:
                pay_rows.append((nid(), tenant, "OUTFLOW", random.randint(lo, hi), CUR,
                                 "TRANSFER", "CONFIRMED", None, cat, who, "Compra de insumos",
                                 None, d.replace(hour=10), 0, None, 0, None))
            d += timedelta(days=7)
        for m_off in range(4):
            md = (TODAY.replace(day=1) - timedelta(days=31 * m_off)).replace(day=5, hour=9)
            if md > NOW:
                continue
            for amt, cat, who, desc in [
                (random.randint(1520000000, 1610000000), "Sueldos", "Personal", "Sueldos del mes"),
                (random.randint(210000000, 240000000), "Sueldos", "AFIP", "Cargas sociales"),
                (random.randint(380000000, 420000000), "Alquiler", "Inmobiliaria", "Alquiler"),
                (random.randint(118000000, 164000000), "Servicios", "Edenor", "Luz y gas"),
                (random.randint(48000000, 62000000), "Servicios", "Contador", "Honorarios"),
                (random.randint(26000000, 38000000), "Servicios", "Telecom", "Internet"),
                (random.randint(155000000, 195000000), "Impuestos", "AGIP", "Ingresos brutos"),
                (random.randint(64000000, 92000000), "Mantenimiento", "Varios", "Reparaciones"),
                (random.randint(38000000, 66000000), "Marketing", "Redes", "Publicidad y fotos"),
                (random.randint(31000000, 39000000), "Seguros", "Aseguradora", "Seguro del local"),
            ]:
                pay_rows.append((nid(), tenant, "OUTFLOW", amt, CUR, "TRANSFER", "CONFIRMED",
                                 None, cat, who, desc, None, md, 0, None, 0, None))

        # ── reservas (algunas futuras, algunas pasadas) ───────────────────
        NOMBRES = ["Familia Gómez", "Laura Benítez", "Mesa Rodríguez", "Sr. Alvarez",
                   "Pareja Ferrari", "Grupo Oficina", "Julieta Paz", "Marcos Rivas"]
        res_rows = []
        for _ in range(18):
            offset = random.randint(-12, 9)
            when = (TODAY + timedelta(days=offset)).replace(
                hour=random.choice([13, 21, 21, 22]), minute=random.choice([0, 30]))
            if offset < 0:
                status = random.choices(["SEATED", "NO_SHOW", "CANCELLED"], weights=[75, 15, 10])[0]
            else:
                status = "PENDING"
            res_rows.append((nid(), tenant, random.choice(NOMBRES),
                             f"11-{random.randint(4000, 6999)}-{random.randint(1000, 9999)}",
                             random.choice([2, 2, 2, 4, 4, 6, 8]), when,
                             "LUNCH" if when.hour < 18 else "DINNER",
                             random.choice(table_ids), status, None, when - timedelta(days=2)))

        # ── fichajes del personal ────────────────────────────────────────
        shift_rows = []
        for offset in range(21):
            d0 = TODAY - timedelta(days=offset)
            for email, role, _n in STAFF:
                if random.random() < 0.18:
                    continue
                cin = d0.replace(hour=11 if role in ("KITCHEN",) else 18,
                                 minute=random.randint(0, 40))
                if cin > NOW:
                    continue
                abierto = offset == 0 and NOW.hour >= cin.hour
                shift_rows.append((nid(), tenant, staff_ids[email], cin,
                                   None if abierto else cin + timedelta(hours=random.randint(7, 9)),
                                   "OPEN" if abierto else "CLOSED",
                                   random.choice(["PRESENCE", "SELF"]), None, None, cin))

        # ── caja: sesiones cerradas + una abierta hoy ────────────────────
        cash_rows, count_rows = [], []
        for offset in range(1, 15):
            d0 = TODAY - timedelta(days=offset)
            sid = nid()
            opened = d0.replace(hour=11, minute=30)
            cash_rows.append((sid, tenant, staff_ids["caja@bravo.demo"], 5000000, CUR, "CLOSED",
                              opened, d0.replace(hour=23, minute=50),
                              staff_ids["caja@bravo.demo"], None, opened))
            for meth in ("CASH", "CARD", "MERCADOPAGO"):
                exp = random.randint(30000000, 90000000)
                count_rows.append((nid(), tenant, sid, meth, exp,
                                   exp + random.choice([0, 0, 0, -150000, 220000])))
        open_sid = nid()
        cash_rows.append((open_sid, tenant, staff_ids["caja@bravo.demo"], 5000000, CUR, "OPEN",
                          TODAY.replace(hour=11, minute=30), None, None, None,
                          TODAY.replace(hour=11, minute=30)))

        # ── liquidaciones de propina ─────────────────────────────────────
        tip_rows = [
            (nid(), tenant, w, random.randint(8000000, 26000000), CUR, "CASH",
             TODAY - timedelta(days=off))
            for off in (7, 14, 21) for w in waiters
        ]

        # ── histórico de precios (para "precios vs inflación") ───────────
        price_rows = []
        for name, price, _c, _w, _s in MENU:
            pid = prod[name][0]
            # precio inicial hace DAYS días, y un ajuste intermedio en la mayoría
            price_rows.append((nid(), tenant, pid, None, int(price * 0.72), CUR,
                               TODAY - timedelta(days=DAYS)))
            if name != "Ojo de bife 400g" and random.random() < 0.8:
                price_rows.append((nid(), tenant, pid, int(price * 0.72), price, CUR,
                                   TODAY - timedelta(days=random.randint(25, 70))))

        total_sales = sum(p[3] for p in pay_rows if p[2] == "INFLOW")
        n_inflow = sum(1 for p in pay_rows if p[2] == "INFLOW")
        month_sales = sum(p[3] for p in pay_rows
                          if p[2] == "INFLOW" and p[12] >= TODAY - timedelta(days=30))
        fc_ratio = {p: food_cost[p] / prod[p][1] for p in food_cost}
        peores = sorted(fc_ratio.items(), key=lambda kv: -kv[1])[:3]

        print(f"PLAN — tenant '{args.tenant}' ({tenant_name})")
        print(f"  período:            {DAYS} días hasta hoy ({TODAY.date()})")
        print(f"  productos:          {len(MENU)}  (cocina/barra)")
        print(f"  insumos:            {len(INGREDIENTS)}")
        print(f"  preparaciones:      {len(PREPARATIONS)}")
        print(f"  proveedores:        {len(SUPPLIERS)}")
        print(f"  mesas:              {len(tables)}")
        print(f"  órdenes:            {len(orders_rows)}")
        print(f"  ítems:              {len(items_rows)}")
        print(f"  cobros + egresos:   {len(pay_rows)}")
        print(f"  comprobantes ARCA:  {len(inv_rows)}")
        print(f"  movimientos stock:  {len(stock_rows)}")
        print(f"  reservas:           {len(res_rows)}")
        print(f"  fichajes:           {len(shift_rows)}")
        print(f"  cajas:              {len(cash_rows)}  (arqueos: {len(count_rows)})")
        print(f"  cambios de precio:  {len(price_rows)}")
        print("\nCOHERENCIA:")
        print(f"  ticket promedio:    {money(total_sales // max(n_inflow, 1))}")
        print(f"  ventas últimos 30d: {money(month_sales)}")
        print(f"  food cost promedio: {sum(fc_ratio.values()) / len(fc_ratio) * 100:.1f}%")
        print("  platos con peor food cost (los que debería marcar el Asesor):")
        for name, r in peores:
            print(f"    · {name}: {r * 100:.1f}%  (precio {money(prod[name][1])}, "
                  f"costo {money(food_cost[name])})")

        if not args.yes:
            print("\nCARTA QUE SE SEMBRARÍA (precio · food cost):")
            for cat in ["Entradas", "Principales", "Guarniciones", "Postres",
                        "Vinos", "Cervezas", "Cócteles", "Bebidas", "Café"]:
                platos = [(n, prod[n][1], food_cost.get(n)) for n, _p, c, _w, _s in MENU
                          if prod[n][2] == cat]
                if not platos:
                    continue
                print(f"  {cat}")
                for n, pr, fc in platos:
                    r = f"{fc / pr * 100:4.1f}%" if fc else "   —"
                    print(f"    {n:<26} {money(pr):>10}   {r}")
            print("\nSIMULACIÓN — no se escribió nada. Volvé a correr con --yes.")
            return

        tx = conn.transaction()
        await tx.start()
        try:
            # ── borrado acotado al tenant ────────────────────────────────
            for table in WIPE_ORDER:
                await conn.execute(f"delete from {table} where tenant_id=$1", tenant)

            # ── personal (se reusa por email, no se borran usuarios) ─────
            for email, role, name in STAFF:
                await conn.execute(
                    "insert into users(id,tenant_id,email,password_hash,role,name,"
                    "email_verified,active,failed_attempts) values($1,$2,$3,NULL,$4,$5,true,true,0)"
                    " on conflict (id) do update set role=excluded.role, name=excluded.name",
                    staff_ids[email], tenant, email, role, name)

            for name, contact in SUPPLIERS:
                await conn.execute(
                    "insert into suppliers(id,tenant_id,name,contact,active)"
                    " values($1,$2,$3,$4,true)",
                    supp[name], tenant, name, contact)

            for name, price, cat, _w, station in MENU:
                await conn.execute(
                    "insert into products(id,tenant_id,name,price_amount,price_currency,category,"
                    "active,station) values($1,$2,$3,$4,$5,$6,true,$7)",
                    prod[name][0], tenant, name, price, CUR, cat, station)

            for name, unit, cost, stock, minq, yld, incl_tax, runit in INGREDIENTS:
                await conn.execute(
                    "insert into ingredients(id,tenant_id,name,unit,stock_qty,min_qty,"
                    "unit_cost_amount,unit_cost_currency,active,yield_pct,cost_includes_tax,recipe_unit)"
                    " values($1,$2,$3,$4,$5,$6,$7,$8,true,$9,$10,$11)",
                    ing[name][0], tenant, name, unit, stock * MIL, minq * MIL, cost, CUR,
                    yld, incl_tax, runit)

            for pname, (yield_qty, items) in PREPARATIONS.items():
                await conn.execute(
                    "insert into preparations(id,tenant_id,name,yield_qty) values($1,$2,$3,$4)",
                    prep[pname][0], tenant, pname, yield_qty * MIL)
                for iname, qty in items:
                    await conn.execute(
                        "insert into preparation_items(id,tenant_id,preparation_id,"
                        "ingredient_id,qty)"
                        " values($1,$2,$3,$4,$5)",
                        nid(), tenant, prep[pname][0], ing[iname][0], qty * MIL)

            for pname, recipe in RECIPES.items():
                pid = prod[pname][0]
                await conn.execute(
                    "insert into recipes(product_id,tenant_id) values($1,$2)", pid, tenant)
                for kind, rname, qty in recipe:
                    await conn.execute(
                        "insert into recipe_items(id,tenant_id,product_id,ingredient_id,"
                        "preparation_id,qty) values($1,$2,$3,$4,$5,$6)",
                        nid(), tenant, pid,
                        ing[rname][0] if kind == "i" else None,
                        prep[rname][0] if kind == "p" else None, qty * MIL)

            for tid, number, tname in tables:
                await conn.execute(
                    "insert into tables(id,tenant_id,number,name,active) values($1,$2,$3,$4,true)",
                    tid, tenant, number, tname)

            # comisiones por método (sin esto la "ganancia real" no existe)
            for method, bps in FEE_BPS.items():
                await conn.execute(
                    "insert into payment_fee_rates(tenant_id,method,fee_bps) values($1,$2,$3)",
                    tenant, method, bps)

            # ARCA conectado + MercadoPago conectado (credenciales de demo)
            await conn.execute(
                "insert into tax_credentials(id,tenant_id,cuit,certificate,private_key,"
                "point_of_sale,fiscal_condition,live_mode) values($1,$2,$3,$4,$5,$6,$7,false)",
                nid(), tenant, "30712345678", "-----DEMO CERT-----", "-----DEMO KEY-----",
                1, "RESPONSABLE_INSCRIPTO")
            await conn.execute(
                "insert into payment_credentials(id,tenant_id,provider,external_account_id,"
                "access_token,public_key,nickname,live_mode,status) "
                "values($1,$2,'mercadopago',$3,$4,$5,$6,false,'CONNECTED')",
                nid(), tenant, "DEMO-1122334455", "DEMO-ACCESS-TOKEN", "DEMO-PUBLIC-KEY",
                tenant_name)

            # ajustes del Asesor calibrados (RevPASH, inflación e IVA incluidos)
            await conn.execute(
                "update advisor_settings set labor_cost_amount=$2, other_fixed_amount=$3,"
                " target_food_cost_bps=3000, seats=40, daily_open_minutes=600,"
                " monthly_inflation_bps=280, default_vat_bps=2100, updated_at=now()"
                " where tenant_id=$1",
                tenant, 1780000000, 900000000)
            hay = await conn.fetchval(
                "select count(*) from advisor_settings where tenant_id=$1", tenant)
            if hay == 0:
                await conn.execute(
                    "insert into advisor_settings(tenant_id,labor_cost_amount,other_fixed_amount,"
                    "currency,target_food_cost_bps,seats,daily_open_minutes,monthly_inflation_bps,"
                    "default_vat_bps) values($1,$2,$3,$4,3000,40,600,280,2100)",
                    tenant, 1780000000, 900000000, CUR)

            await conn.copy_records_to_table(
                "orders", records=orders_rows,
                columns=["id", "tenant_id", "table_id", "waiter_id", "status", "currency",
                         "created_at"])
            await conn.copy_records_to_table(
                "order_items", records=items_rows,
                columns=["id", "tenant_id", "order_id", "product_id", "name", "unit_price_amount",
                         "quantity", "note", "position", "created_at", "status", "station",
                         "sent_at", "ready_at"])
            await conn.copy_records_to_table(
                "payments", records=pay_rows,
                columns=["id", "tenant_id", "direction", "amount", "currency", "method", "status",
                         "order_id", "category", "counterparty", "description", "external_ref",
                         "created_at", "tip_amount", "cash_session_id", "fee_amount", "net_amount"])
            await conn.copy_records_to_table(
                "sale_facts", records=fact_rows,
                columns=["id", "tenant_id", "order_id", "order_item_id", "product_id",
                         "product_name", "category", "quantity", "unit_price_amount", "line_amount",
                         "food_cost_amount", "currency", "waiter_id", "table_id", "occurred_at",
                         "created_at"])
            await conn.copy_records_to_table(
                "invoices", records=inv_rows,
                columns=["id", "tenant_id", "type", "point_of_sale", "number", "doc_type",
                         "doc_number", "concept", "net_amount", "vat_amount", "total_amount",
                         "currency", "vat_items", "status", "cae", "cae_expiration", "rejection",
                         "order_id", "issued_at", "created_at"])
            await conn.copy_records_to_table(
                "stock_movements", records=stock_rows,
                columns=["id", "tenant_id", "ingredient_id", "direction", "reason", "qty",
                         "order_id", "unit_cost_amount", "unit_cost_currency", "note",
                         "created_at"])
            await conn.copy_records_to_table(
                "reservations", records=res_rows,
                columns=["id", "tenant_id", "customer_name", "customer_phone", "party_size",
                         "reserved_at", "turn", "table_id", "status", "note", "created_at"])
            await conn.copy_records_to_table(
                "shifts", records=shift_rows,
                columns=["id", "tenant_id", "user_id", "clock_in_at", "clock_out_at", "status",
                         "source", "note", "adjusted_by", "created_at"])
            await conn.copy_records_to_table(
                "cash_sessions", records=cash_rows,
                columns=["id", "tenant_id", "opened_by", "opening_float_amount", "currency",
                         "status", "opened_at", "closed_at", "closed_by", "note", "created_at"])
            await conn.copy_records_to_table(
                "cash_counts", records=count_rows,
                columns=["id", "tenant_id", "cash_session_id", "method", "expected_amount",
                         "counted_amount"])
            await conn.copy_records_to_table(
                "tip_payouts", records=tip_rows,
                columns=["id", "tenant_id", "waiter_id", "amount", "currency", "method",
                         "created_at"])
            await conn.copy_records_to_table(
                "product_price_changes", records=price_rows,
                columns=["id", "tenant_id", "product_id", "old_price_amount", "new_price_amount",
                         "currency", "changed_at"])

            await tx.commit()
            print("\nLISTO ✅  — el tenant quedó resembrado.")
            print("   Snapshots de Finanzas: POST /finance/snapshots/rebuild")
            print("   Diagnósticos del Asesor: POST /advisor/diagnostics/rebuild")
        except Exception:
            await tx.rollback()
            raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
