# Los números están bien calculados; el problema son los insumos

**Proyecto:** BRAVO · **Fecha:** 2026-09-10 · **Rama:** `main` · **Commit base:** `202c09e`
**Alcance:** todo lo que el sistema muestra como cifra — KPIs financieros, costeo de recetas,
proyección de ventas, arqueo, propinas, facturación, precios y menu engineering.
**Modo:** solo lectura — no se modificó ningún archivo.

El pedido era asegurar que un local que contrate el servicio pueda confiar en lo que ve.

---

## Veredicto

**No encontré ninguna fórmula mal implementada.** El proyecto tiene una disciplina de plata
poco común: enteros en unidad mínima en todo el núcleo, IVA simétrico entre ventas y costos,
reversas exactas, y una guarda que impide que el LLM invente cifras.

El riesgo está en otro lado: **hay números calculados perfecto sobre datos incompletos, y la
pantalla no lo dice.** Para el objetivo de este documento —que el dueño confíe— eso pesa igual
que un error de cuenta, porque el efecto es el mismo: decide sobre algo que no es.

Y hay un caso que rompe la confianza de frente: el margen neto ignora los gastos que el dueño
carga día a día.

---

## Resumen de hallazgos

Ordenado por cuánto distorsiona una decisión, no por dificultad de arreglo.

| Ref. | Severidad | Hallazgo | Efecto |
|---|---|---|---|
| N1 | 🔴 Crítica | Los egresos registrados no entran al margen neto | El margen no reacciona a los gastos reales |
| N2 | 🔴 Crítica | El costo de personal cuenta solo a quien tenga tarifa cargada | Margen inflado, sin aviso |
| N3 | 🟠 Alta | La rotación de inventario usa el stock de hoy para cualquier período | Un período pasado da un número que no es el suyo |
| N4 | 🟠 Alta | La merma se valoriza al costo actual, no al del día | Convive con un COGS congelado: dos bases |
| N5 | 🟠 Alta | No se define si los costos fijos van con IVA o sin IVA | El margen es ambiguo, no incorrecto |
| N6 | 🟡 Media | La guarda anti-alucinación se puede burlar recombinando fragmentos | El Asesor podría citar un % falso |
| N7 | 🟡 Media | Prorrateo con mes de 30 días | Comparar meses no es parejo (±3-7%) |
| N8 | 🟡 Media | RevPASH usa ventas brutas; los márgenes, netas | Dos bases en la misma pantalla |
| N9 | 🟡 Media | El turno abierto no cuenta en el costo de personal | El costo de hoy siempre está incompleto |
| N10 | 🟡 Baja | Redondeo bancario en el dominio vs medio-arriba en el adapter de MP | Diferencias de un centavo en conciliación |

---

## 1 · Lo que verifiqué y está bien

Vale enumerarlo, porque en una auditoría lo que no se menciona queda en duda.

- ✅ **La plata nunca es flotante.** `Money` es un entero en unidad mínima + moneda ISO, rechaza
  negativos y no suma monedas distintas (`domain/shared/money.py`). No hay fuga de centavos.
- ✅ **El IVA cierra exacto.** `split_vat` calcula el neto y deriva el IVA como `total − neto`,
  así que `neto + IVA` reconstruye el total siempre (`domain/invoice/taxation.py:18-23`).
- ✅ **Ventas y costos van en la misma base.** Las dos se netean de IVA antes de cualquier
  ratio (`domain/advisor/kpis.py`, propiedades `_net_sales` / `_net_food_cost`). Mezclarlas es
  el error clásico de este tipo de sistema y acá no está.
- ✅ **El ticket promedio queda bruto a propósito** — es lo que paga el cliente — y está
  documentado como decisión, no como descuido.
- ✅ **El punto de equilibrio se desnetea** con la proporción bruto/neto del período, para que
  sea comparable con lo que el dueño factura. Detalle fino, bien resuelto.
- ✅ **Las fórmulas son las estándar del rubro:** prime cost = food + labor; margen de
  contribución = (ventas − variables)/ventas; equilibrio = fijos / margen de contribución.
- ✅ **Costeo de recetas multinivel** con rendimiento (merma), conversión de unidades KG→G /
  L→ML y recetas madre anidadas, con guarda anti-ciclo (`domain/inventory/costing.py`).
- ✅ **El consumo de stock convierte bien:** pasa de unidad de receta a unidad de compra antes
  de generar el movimiento (`application/inventory/consume.py:82`).
- ✅ **La merma usa las unidades correctas** (`qty × costo / 1000` sobre movimientos ya
  expresados en unidad base). Lo verifiqué contra `consume.py` porque parecía un bug y no lo es.
- ✅ **Arqueo de caja correcto:** esperado = ventas + propinas + fondo inicial + movimientos
  manuales, con las propinas expuestas aparte para poder separarlas
  (`application/cashier/use_cases.py:44-47`).
- ✅ **La propina no cancela deuda de la comanda** y no entra al libro de ventas — no es
  ingreso del local. Y existe el circuito de liquidación con saldo pendiente por mozo.
- ✅ **El tipo de comprobante sigue la regla de AFIP:** emisor monotributo → C; RI → A si el
  receptor tiene CUIT, si no B.
- ✅ **Menu engineering es honesto.** Se niega a clasificar un plato sin costo confirmado, con
  ratio fuera de banda o con pocas ventas: lo manda a "sin datos" en vez de inventar una
  categoría (`frontend/src/features/products/menu-engineering.ts:91-105`).
- ✅ **Reabrir una comanda revierte todo y es simétrico:** descuenta el snapshot del día con
  todos los campos negados antes de borrar los hechos de venta
  (`application/analytics/projection.py:227-244`).
- ✅ **El Asesor no puede inventar cifras.** Si el texto del LLM contiene un número que no está
  en el cálculo determinístico, se descarta y se usa la versión de plantilla; cualquier fallo
  del LLM cae al mismo lugar (`infrastructure/advisor/claude_narrator.py:37-38`). **Es
  exactamente la guarda que este producto necesita, y ya está construida.**
- ✅ **La cantidad de comandas sale de los hechos de venta** (`COUNT(DISTINCT order_id)`), no
  del estado de la orden — así que el canal prepago, que nunca llega a PAID, no descuadra el
  ticket promedio.

---

## 2 · Los hallazgos

### N1 — 🔴 Los egresos que el dueño registra no afectan su margen

**Qué ve el dueño.** En la misma pantalla de Finanzas conviven "Tu ganancia neta del período"
y "Distribución de gastos". Parecen el mismo universo. No lo son.

**Qué pasa por dentro.** El margen neto se calcula con el estimado mensual que el dueño cargó
una vez en Ajustes (`application/advisor/report.py:185-195`, `prorate_monthly` sobre
`monthly_labor_cost` y `monthly_other_fixed_costs`). Los egresos registrados —los que alimentan
el donut, "los 3 gastos que más cambiaron" y el "Gastaste hoy" del Inicio— salen de la tabla de
pagos y **no entran en ninguna parte del margen**.

**Consecuencia.** El dueño carga un gasto de $500.000 y el margen no se mueve. Al revés, el
margen puede estar usando un número que cargó hace seis meses y nunca actualizó. Las dos cifras
son correctas por separado y juntas construyen una idea falsa.

**Qué haría.** Decidir cuál es la fuente de verdad de los costos fijos y decirlo en la pantalla.
Si es el estimado, el bloque de gastos tiene que aclarar que es informativo. Si son los egresos
reales, el margen tiene que leerlos. Hoy no hay respuesta.

---

### N2 — 🔴 El costo de personal cuenta solo a los empleados con tarifa cargada

El propio código lo documenta: *"suman los empleados con rate cargado (los demás no aportan —
cargar todos los rates para un número completo)"*
(`infrastructure/persistence/labor_cost_repo.py`). La consulta filtra por
`hourly_rate_amount IS NOT NULL`.

**El problema no es el código, es que la pantalla no lo dice.** Si 3 de 10 empleados tienen
tarifa, el costo de personal es el de 3, el porcentaje se muestra como si fuera completo, y el
margen queda inflado.

**Agravante.** Si *nadie* fichó en el período, el sistema cae al estimado mensual
(`labor_override=labor_real or None`, `report.py:128`). O sea que el número salta entre dos
definiciones distintas —costo real fichado vs estimado mensual— según quién fichó ese mes, sin
avisarlo.

---

### N3 — 🟠 La rotación de inventario de un período pasado usa el stock de hoy

`rotación = COGS del período / valor del inventario` (`application/finance/use_cases.py:141`).

El numerador respeta el período. El denominador no puede: el puerto que lo provee **no recibe
fechas** (`total_value(tenant_id)`, `use_cases.py:115-119`). Siempre es el inventario de ahora.

**Consecuencia.** Mirás enero en marzo y obtenés un número que no es el de enero. Y si recibiste
una entrega grande ayer, la rotación de *todos* los períodos empeora de golpe.

A favor: la pantalla no finge tendencia (muestra delta 0 a propósito), así que al menos no
inventa una comparación.

---

### N4 — 🟠 La merma se valoriza al costo de hoy, el COGS al del día de la venta

El costo de la mercadería vendida se **congela** en la proyección: cada venta guarda el food
cost del momento. Correcto y deliberado.

La merma no: se calcula con `IngredientORM.unit_cost_amount`, el costo **actual** del insumo
(`infrastructure/persistence/advisor_repo.py:40-58`).

**Consecuencia.** Con la inflación argentina, la merma de hace seis meses figura a precio de hoy
y convive en la misma pantalla con un costo de ventas congelado. Dos bases distintas sumando al
mismo margen. El ratio de mermas de un período pasado cambia solo con el tiempo.

---

### N5 — 🟠 Nadie define si los costos fijos se cargan con IVA o sin IVA

El campo se rotula *"Otros costos fijos del mes (alquiler, servicios…)"*
(`i18n/locales/es/advisor.ts:15`) y su importe se resta de **ventas netas de IVA**
(`domain/advisor/kpis.py`, `net_margin_amount`).

Para un Responsable Inscripto el IVA de los servicios es crédito fiscal: el costo real es el
neto, y cargar el bruto empeora el margen hasta un 21% de esa línea. Para un monotributista es
al revés: el IVA es costo y corresponde el bruto.

**No está mal calculado — está indefinido.** El mismo campo significa cosas distintas según el
régimen y nadie se lo dice al dueño.

---

### N6 — 🟡 La guarda anti-alucinación se puede burlar recombinando fragmentos

La guarda extrae los números con `re.findall(r"\d+", text)` y rechaza el texto del LLM si
aparece algún dígito que no esté en la base (`claude_narrator.py:21`).

El problema es que `\d+` parte por los separadores: `$19.951.654` se guarda como
`{19, 951, 654}`. El modelo podría escribir *"un 19% de food cost"* y **pasar el control**,
porque "19" existe como grupo de miles de otra cifra.

No inventa de la nada, pero puede recombinar fragmentos en una afirmación falsa. Comparar
números completos (con separadores normalizados) en vez de corridas de dígitos lo cierra.

---

### N7 a N10 — menores

**N7 · Prorrateo con mes de 30 días.** `prorate_monthly` divide por 30 fijo
(`domain/advisor/kpis.py`). En un mes de 31 días los costos fijos se inflan 3,3%; en febrero se
achican 6,7%. Comparar meses entre sí no es del todo parejo.

**N8 · RevPASH usa ventas brutas** (`use_cases.py:133`, `cur.sales_amount`) mientras todos los
márgenes usan netas. Misma pantalla, dos bases.

**N9 · El turno abierto no cuenta.** El costo de personal filtra `status == CLOSED`, así que el
costo de hoy está siempre incompleto hasta que el último empleado ficha la salida.

**N10 · Redondeo inconsistente.** El dominio usa `round()` de Python (redondeo bancario, 0,5 al
par) y el adapter de MercadoPago usa `ROUND_HALF_UP`. Ninguno está mal; que convivan puede
producir diferencias de un centavo en una conciliación.

---

## 3 · La conclusión que importa

El proyecto **ya tiene** el mecanismo correcto para todo esto, y funciona.

En Productos, un plato sin costo respaldado por compras reales no entra a la plata: se muestra
como "sin datos" y la pantalla informa la cobertura (`coverage_bps`, `cost_confirmed` en
`application/inventory/food_cost.py:22-28`). En producción se lee *"21 de 21 platos con costo
confirmado"*. Esa es exactamente la disciplina que este documento pide.

**Está aplicada a la mitad de la ecuación.** El food cost tiene su medidor de cobertura. El
costo de personal, los costos fijos y —por lo tanto— el prime cost, el punto de equilibrio y el
margen neto, no tienen ninguno.

> Si el dueño va a confiar en el margen, la pantalla tiene que decirle sobre qué está parado:
> *"calculado sobre 3 de 10 empleados con tarifa cargada"*, *"tus gastos registrados no entran
> en este número"*, *"rotación calculada sobre el inventario de hoy"*.

Extender el medidor de cobertura del food cost al resto de los insumos del margen vale más que
cualquiera de los diez hallazgos por separado, y es construir sobre algo que ya existe.

---

## 4 · Orden de trabajo sugerido

1. **N1** — decidir la fuente de verdad de los costos fijos y hacerla explícita en la pantalla.
   Es el único hallazgo donde el dueño puede tomar una decisión equivocada creyendo que el
   sistema le respondió.
2. **N2** — exponer la cobertura del costo de personal, igual que se hace con el food cost.
3. **N5** — definir la base (con/sin IVA) del campo de costos fijos y decirlo en el rótulo.
   Es texto, no cálculo.
4. **N3 y N4** — dos decisiones del mismo tipo: qué hacer con un dato que sí tiene historia
   (congelar el costo de la merma) y con uno que no la tiene (guardar valor de inventario por
   período).
5. **N6 a N10** — higiene. Ninguno cambia una decisión hoy.

---

Auditoría de solo lectura sobre `backend/app`, `frontend/src` y `mobile/lib` en el commit
`202c09e`. No se modificó ningún archivo. Cada hallazgo tiene su referencia verificada contra el
código en el árbol de trabajo.
