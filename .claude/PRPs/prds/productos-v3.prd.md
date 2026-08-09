# Productos v3 — Motor de costos real + carta que decide

> Fuente: `~/Downloads/PANTAL~2.TXT` ("PANTALLA DE PRODUCTOS — ESPECIFICACIÓN Y CORRECCIONES", Wellnod v1), auditoría experta de `/app/products` en producción + doc preliminar de 9 niveles. Verificado contra el código real (commit `af729e1`, Productos v2 A/B/C ya en `main`).

## Problem Statement

El dueño de un restaurante decide precios, recetas y qué platos empujar/sacar mirando la pantalla Productos. Hoy esa pantalla le muestra **números que no le cierran**: bloques que se contradicen (un bloque dice "no hay ventas en 30 días", otro muestra $15M/día), márgenes calculados sobre costos sin merma ni IVA (mienten para arriba 10–25%), y clasificaciones que comparan un café contra una milanesa. El costo de no resolverlo es directo: **si el dueño ve un número que no le cierra con su caja, deja de creernos y no lo recupera** — y perdemos el diferenciador que nadie más da (food cost real + menu engineering en pesos).

## Evidence

- **Verificado en código** (agente de exploración, este proyecto): el catálogo muestra solo precio (falta Costo/Te deja/Vendidos); la clasificación compara contra el promedio de **toda la carta** con umbrales fijos (0.55/0.45), no por categoría; **no hay** `yield_pct` de merma ni IVA en el costeo; **no hay** estado estimado/confirmado de costo; cada bloque usa su **propia ventana** de tiempo (menu eng 30d, rotación todo-el-historial, precios per-producto); nombre de producto valida solo `min_length=1` (por eso entró "aaaaa"); `station` default `KITCHEN` (por eso todo quedó en "Cocina").
- **Observado en producción** (spec, sección 0): contradicción entre bloques (B1), magnitud rara $15.894.600/sábado (B2), "plato estrella" repite café con leche 5/7 días (B3), fila basura "aaaaa/2aaa" (B5).
- **Ya construido y bien** (spec + memoria): catálogo (29 productos), recetas madre con rendimiento (Tanda C), precios vs inflación con 1 campo (Tanda B), rotación por día (Tanda B), menu engineering 5 categorías frontend (Tanda A), empty states correctos.

## Proposed Solution

Rehacer Productos alrededor de un **motor de costos correcto** (merma, conversión de unidades, IVA neto, versionado de receta, estado estimado/confirmado) y una **regla de honestidad transversal**: nada de plata sobre costos no confirmados, cobertura siempre visible, comparaciones dentro de la categoría, y "lo que ya pasó" antes que "lo que va a pasar". Encima de ese motor, actualizar los bloques que ya existen (menu engineering, precios vs inflación, rotación, catálogo, ficha, hero) a las definiciones del spec. Estructura: de 9 niveles a **5 bloques** con **un selector de período único**. Se construye por fases; los tres bloques que funcionan sin ventas (costos, precios vs inflación, catálogo) dan valor desde el día uno.

## Key Hypothesis

Creemos que **un food cost real (con merma+IVA) y una carta clasificada por categoría, en pesos y solo sobre costos confirmados**, van a **hacer que el dueño confíe y actúe sobre la pantalla** (subir un precio rezagado, mejorar una receta de alto volumen). Lo sabremos cuando el dueño **confirme costos de ≥70% de su carta** y **aplique al menos un cambio de precio o receta sugerido por mes**.

## What We're NOT Building

- **Mapeo POS→producto (Ticket 2) en v1** — nosotros somos el POS: `OrderItem` ya apunta exacto a `product_id`, no hay nombre externo que matchear. Queda como **fase futura condicional** (solo si se ingiere un POS externo/legacy). Sí se hace el "chequeo de sanidad" de categoría con 0 ventas.
- **Costo de mano de obra / tiempo de preparación por plato** — se nombra en la ficha como pendiente, no se calcula (es otro dominio; ya tenemos labor a nivel Finanzas).
- **Control de stock / inventario como producto** — fuera de alcance (ya hay stock básico de insumos; el consumo de stock de preparaciones anidadas sigue diferido).
- **Sugerencia de precio óptimo automática** — primero hay que juntar historial de cambios (elasticidad).
- **Reemplazo automático de ingredientes por alternativas más baratas.**

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Cobertura de costos confirmados | ≥70% de platos por tenant activo | `cost_confirmed=true / total productos` |
| Contradicciones entre bloques | 0 | Un solo `período` global; auditoría visual |
| Exactitud de margen (con merma+IVA) | margen mostrado = margen real ±2% | test de paridad + revisión con dueño piloto |
| Acción del dueño sobre la pantalla | ≥1 cambio precio/receta aplicado por mes | `product_price_changes` + edición de receta |

## Open Questions

- [ ] IVA neto: ¿el precio de venta se guarda con IVA (como hoy) y se netea al calcular margen, o migramos a guardar neto? (spec pide "todo neto internamente, mostrar con IVA").
- [ ] Merma: ¿defaults por tipo de ingrediente (carne/verdura/seco) — de dónde sale la tabla de defaults?
- [ ] Redondeo de precios sugeridos: confirmar múltiplos (default spec: 50 para <$5.000, 100 arriba).
- [ ] Propagación de costos: ¿sincrónica multinivel (como hoy) alcanza, o hace falta la cola async + cron nocturno? (decisión de infra ya analizada — arrancar sync).

---

## Users & Context

**Primary User**
- **Who**: Dueño/encargado (rol OWNER/MANAGER) de un restaurante/café PyME argentino, no técnico, que carga su carta y sus compras y quiere saber qué le deja cada plato.
- **Current behavior**: Mira precios "a ojo", no conoce su food cost real, ajusta precios tarde y por inflación general, no sabe qué plato de alto volumen le está comiendo el margen.
- **Trigger**: Cierre de mes, una compra que subió de golpe, o "siento que trabajo mucho y no me queda nada".
- **Success state**: "Sé cuánto me deja cada plato después de los ingredientes, cuáles empujar, y qué precios tengo rezagados contra lo que me subieron MIS insumos."

**Job to Be Done**
Cuando **noto que mis costos subieron y no sé si mis precios acompañan**, quiero **ver el margen real de cada plato y qué precios están rezagados**, para **ajustar la carta sin regalar plata ni espantar clientes**.

**Non-Users**
El mozo/cocina (no deciden carta), y el dueño que aún no cargó carta ni compras (para ese, es onboarding, no análisis).

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Selector de período único global (B1) | Sin esto, bloques contradictorios rompen confianza |
| Must | Merma (`yield_pct`) + conversión de unidades + IVA neto en el costeo (T1.1–1.3) | Sin esto el margen miente; es el cimiento |
| Must | Estado estimado/confirmado + cobertura visible (Regla 6, T1.7) | Nada de plata sobre costos inventados |
| Must | Menu engineering por categoría + estados explícitos + piso mínimo (T3) | El diferenciador; hoy compara mal |
| Must | Catálogo con Costo/Te deja/Vendidos + buscador/filtros (B6/B7, T7) | Sin eso la tabla no sirve para decidir |
| Should | Precios vs inflación con canasta propia + redondeo + bulk seguro (T4) | Lo más fuerte para AR; ya esbozado |
| Should | Versionado de receta + snapshot histórico correcto (T1.6) | Sin esto el histórico es ficción |
| Should | Rotación por sobre-índice (T6) + hero verificable (T8) | Insights accionables reales |
| Should | Ficha completa + alertas de ingrediente (T7) | "El bife subió 12%, perdés $4/plato" es muy vendible |
| Could | Costo estimado por IA con desglose (T1.7) | Baja fricción de carga; reusa LLM Fase 9 |
| Could | Propagación async + cron nocturno | Optimización; sync alcanza para arrancar |
| Won't (v1) | Mapeo POS externo (T2) | Somos el POS; condicional a futuro |
| Won't (v1) | Elasticidad honesta (T5) | Necesita historial de ≥4 cambios de precio |
| Won't (v1) | IPC/INDEC externo | Integración de dato de terceros; la canasta propia lo cubre mejor |

### MVP Scope

Fases 1–2: bugs baratos + motor de costos con merma/IVA/conversión y estado confirmado. Con eso el dueño ya ve **food cost real y confiable** y cobertura — el núcleo de la confianza.

### User Flow

1. Dueño abre Productos → elige período (global).
2. Hero: "De tus 68 platos, 12 son tu motor y te dejaron $2.140.000 este mes" (solo si cobertura ≥70%; si no, "te faltan N platos con costo confirmado").
3. 5 categorías de acción (por categoría de carta) → entra a una → ve platos con Costo/Te deja/Vendidos.
4. Ve un precio rezagado (canasta propia) → simula → aplica (con preview + undo).
5. Confirma costos estimados que faltan → sube la cobertura.

---

## Technical Approach

**Feasibility**: **HIGH** — todo se apoya en infra existente.

**Architecture Notes**
- **Motor de food cost ya es puro y aislado**: `domain/inventory/costing.py` (`food_cost()` multinivel + `resolve_preparation_costs()` con guard anti-ciclo). Merma/IVA/conversión se extienden ahí, con test de paridad para no romper Finanzas.
- **Snapshot por venta ya existe**: `sale_facts` congela `food_cost` al pagar (`ProjectOrderSales`). Falta `recipe_version` para el histórico correcto (T1.6).
- **Precios ya se registran**: `product_price_changes` (Tanda B) + `PUT /products/{id}/price`. Falta `batch_id`/`reason` y el bulk con undo (T4.3/4.4).
- **LLM disponible** (Fase 9) para el costo estimado por IA con desglose (T1.7).
- **Reglas de honestidad** en un helper único (`can_show_share` / cobertura), no replicado por bloque — mismo criterio que el CRM.
- Todo agregado lee de tablas precalculadas (incremental por evento como hoy; cron nocturno opcional, ya analizado).

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Extender `costing.py` (merma/IVA) rompe números de Finanzas ya en prod | M | Test de paridad + backward-compatible + suite completa verde por slice |
| Migrar a IVA neto toca precios existentes | M | Guardar neto derivado, mostrar con IVA; migración con backfill idempotente |
| Bulk "aplicar a todos" mal aplicado en temporada | M | Preview obligatorio + una transacción + `batch_id` + undo 24h |
| Versionado de receta agranda el modelo | M | `recipe_version` incremental + snapshot ya existente en sale_facts |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Bugs P0 | Período único (B1), estación default (B4), validación nombre (B5), catálogo con Costo/Te deja/Vendidos + buscador/filtros (B6/B7) | complete | - | - | `reports/productos-v3-fase-1-bugs-report.md` |
| 2 | Motor de costos v2 | Merma `yield_pct` (T1.2), conversión de unidades (T1.1), IVA neto (T1.3), costo de reposición + histórico de insumo (T1.4), tope de profundidad (T1.5), versionado de receta + snapshot (T1.6) | pending | - | 1 | - |
| 3 | Costo confirmado + IA | Estado estimado/confirmado + cobertura visible (Regla 6), costo estimado por IA con desglose (T1.7) | pending | with 4 | 2 | - |
| 4 | Menu engineering v2 | Comparación por categoría (T3.1), estados explícitos + piso mínimo + SIN DATOS (T3.2), "no vendido" con contexto + flag estacional (T3.3), quitar bloques duplicados (T3.4), naming "después de los ingredientes" (T3.5) | pending | with 3 | 2 | - |
| 5 | Precios vs inflación v2 | Canasta propia del restaurante (T4.1b), redondeo a múltiplos (T4.2), "aplicar a todos" con preview+transacción+undo 24h (T4.3), `price_history` con reason/batch_id (T4.4) | pending | - | 2 | - |
| 6 | Rotación + Hero | Rotación por sobre-índice (T6, reemplaza plato estrella / arregla B3), hero verificable + oportunidad separada + gate cobertura ≥70% (T8) | pending | - | 2, 4 | - |
| 7 | Ficha completa | Receta con desglose + histórico de costos versionado + historial de precios + alertas de ingrediente ("el bife subió 12%") + "costos viejos si no cargás compras hace 60d" (T7) | pending | - | 2, 3 | - |
| 8 | Infra async (futuro) | Cola de propagación de costos + cron nocturno Railway (propagación async T1.5 + acciones precomputadas) | pending | - | 2 | - |
| 9 | Elasticidad honesta (futuro) | Participación, diff-in-diff, deflactar, mínimos (4 cambios/6 semanas/30u), mostrar rango (T5) | pending | - | 5 | - |
| 10 | IPC + POS (futuro) | IPC/INDEC como 2ª referencia (T4.1a), mapeo POS→producto para ingesta externa (T2) | pending | - | 2, 5 | - |

### Phase Details

**Phase 1 — Bugs P0**
- **Goal**: Que la pantalla deje de contradecirse y el catálogo sirva para decidir.
- **Scope**: Un `period` global compartido por los 3 bloques; sacar/forzar el default de estación; validar nombre (min 2, no todo-igual) + limpiar fila basura; agregar columnas Costo/Te deja/Vendidos + buscador + filtros al catálogo (el dato ya existe en menu engineering).
- **Success signal**: Un solo selector; rotación y menu eng leen la misma ventana; catálogo con las 3 columnas y filtrable.

**Phase 2 — Motor de costos v2**
- **Goal**: Food cost real (no subestimado 10–25%).
- **Scope**: `yield_pct` por ingrediente + fórmula `costo_real = (qty/yield_pct) * costo_base`; tabla de conversión de unidades por familia (no g↔ml sin densidad); IVA neto (guardar neto, check "incluye IVA" en compra, mostrar con IVA); costo de reposición (último precio, ya default) + histórico de costo de insumo; tope de profundidad 5 + ciclos (ya ✅); `recipe_version` + snapshot al vender.
- **Success signal**: Test de paridad verde; margen de un plato con hueso/merma baja correctamente; Finanzas no cambia.

**Phase 3 — Costo confirmado + IA**
- **Goal**: Cero plata sobre costos inventados.
- **Scope**: Estado `cost_confirmed` (estimado/confirmado) en producto; los estimados no entran en conclusiones de plata y se muestran en gris; cobertura "N de M confirmados" visible; costo estimado por IA que devuelve **desglose de ingredientes** (no un número suelto), reusando LLM de Fase 9.
- **Success signal**: Un plato con costo estimado no aparece en el hero ni suma a "te dejó $X"; la cobertura se muestra.

**Phase 4 — Menu engineering v2**
- **Goal**: Clasificación útil (café vs café).
- **Scope**: `ventas_rel`/`margen_rel` contra el promedio **de su categoría de carta**; categorías con <4 productos → "Otros"; estados FUNCIONA/OPORTUNIDAD/ESTABLE/REVISAR/NO VENDIDO/SIN DATOS con piso mínimo (default 10u/mes o costo no confirmado → SIN DATOS); "no vendido" descarta alta <30d y estacional (flag nuevo); quitar Top 3 y "asesinos de margen" (duplicados); naming.
- **Success signal**: Un café deja de competir contra platos principales; nada se clasifica con <N ventas.

**Phase 5 — Precios vs inflación v2**
- **Goal**: "Tus insumos subieron 14%, tus precios 8%, perdés $X/venta" — defendible y propio.
- **Scope**: Canasta propia (variación ponderada de SUS insumos desde recetas+compras); redondeo configurable; "aplicar a todos" con preview de la lista completa + una transacción + log `batch_id` + undo 24h; `price_history` con `reason`/`batch_id`.
- **Success signal**: Un aumento masivo se previsualiza, se aplica atómico y se puede deshacer.

**Phase 6 — Rotación + Hero**
- **Goal**: Insights que no repitan la obviedad.
- **Scope**: Sobre-índice `indice_dia = participación_día / participación_semana` (>1.3 / <0.7), mínimos 20 ventas + 4 semanas; facturación por día aparte (dotación); hero en dos partes (verificable + oportunidad marcada), gate cobertura ≥70%.
- **Success signal**: "El lomo vende el triple los sábados" en vez de "café con leche estrella otra vez".

**Phase 7 — Ficha completa**
- **Goal**: La ficha del plato como herramienta de decisión.
- **Scope**: Desglose de receta + recetas anidadas (ya ✅) + rendimiento del mes (con cobertura) + histórico de costos desde snapshots versionados + historial de precios + alertas de ingrediente + aviso de costos viejos (compras >60d).
- **Success signal**: El dueño ve por qué cambió el costo de un plato y qué ingrediente lo movió.

**Phase 8 — Infra async (futuro)**
- **Goal**: Sacar la propagación pesada del request.
- **Scope**: Cola de recálculo de padres afectados + cron nocturno en Railway (servicio aparte, entrypoint `python -m app.jobs.nightly`, itera tenants, reusa rebuild use cases). Ver `plan-desktop` / análisis de cron ya hecho.
- **Success signal**: Cambiar el costo de un insumo con 50 platos afectados no bloquea la UI.

**Phase 9 — Elasticidad honesta (futuro)**
- **Goal**: Anticipar el efecto de un cambio de precio sin mentir.
- **Scope**: Medir participación (no unidades), diff-in-diff vs resto de categoría, deflactar por inflación del período, mínimos (4 cambios/6 semanas antes-después/30u), mostrar rango con nº de observaciones. Si no se cumplen mínimos: mostrar historial crudo + "todavía no tenemos suficientes cambios tuyos".
- **Success signal**: Nunca un punto único; siempre rango + observaciones, o historial honesto.

**Phase 10 — IPC + POS (futuro)**
- **Goal**: Dejar armado lo condicional a terceros/ingesta externa.
- **Scope**: IPC/INDEC (división Restaurantes y hoteles) como 2ª referencia junto a la canasta propia; `pos_product_map` + matcheo por similitud + cola de "sin identificar" + sanity check de categoría, para cuando se ingiera un POS externo.
- **Success signal**: Documentado y construible; se activa si aparece un POS externo o feed de IPC.

### Parallelism Notes

Fases 3 y 4 pueden ir en paralelo (ambas dependen de 2; una toca costo/IA, otra clasificación). 5 depende solo de 2. 6 y 7 dependen de 2 (+4/+3). Las fases 8–10 son "futuro" independientes entre sí; se activan por demanda/datos.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| POS mapping en v1 | No (futuro condicional) | Construir ahora | Somos el POS; OrderItem→product es exacto |
| Costo a usar | Último precio (reposición), configurable | Promedio ponderado | En inflación, el promedio subestima reponer |
| IVA | Todo neto interno, mostrar con IVA | Ignorar IVA | Sin esto el margen se va 21% de lado |
| Inflación | Canasta propia primero, IPC después | Solo IPC | La canasta propia es defendible y nadie más la da |
| Propagación | Sincrónica multinivel ahora, async luego | Async desde ya | Sync ya funciona; async es optimización |
| Elasticidad | Diferida hasta tener ≥4 cambios | Mostrar con 2 | Con 2 observaciones es casualidad con formato de dato |

---

## Research Summary

**Market Context**: El diferenciador (food cost real + menu engineering en pesos + precios vs inflación con canasta propia) es lo que la competencia AR no da. La postura de honestidad (cobertura visible, nada de % inflado, verificable > prometido) es defensa de confianza, no cosmética.

**Technical Context**: Motor de food cost puro y aislado (`costing.py`), snapshot por venta (`sale_facts`), registro de precios (`product_price_changes`), LLM (Fase 9) y recetas madre con rendimiento (Tanda C) ya existen. La v3 extiende ese motor y actualiza los bloques a las definiciones del spec, sin re-arquitectura.

---

*Generated: 2026-08-04*
*Status: DRAFT — cubre todos los puntos del spec, incluidos los diferidos como fases 8–10*
