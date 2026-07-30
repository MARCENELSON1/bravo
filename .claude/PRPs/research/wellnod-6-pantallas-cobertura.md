# Wellnod — Las 6 pantallas: spec de producto vs. lo construido

**Fecha:** 2026-07-29 · **Fuente:** `~/Desktop/BRAVO/proyecto Well Nod 2026/` (5 `.docx` de spec de pantalla + 2 `.xlsx` de negocio).
**Método:** analizado TODO — texto completo de los 7 archivos + **las 27 imágenes** embebidas (mockups ASCII detallados: 10 Finanzas, 11 Productos, 6 Reportes; Home y Clientes eran solo texto, sin mockups).

Este doc es el **checklist de roadmap del producto de cara al dueño**: las 6 pantallas que el pricing define como Wellnod (Home + Finanzas + Clientes + Productos + IA Insights + Reportes). No cubre la capa operativa (comandas, KDS, mesas, caja, fichaje, cobros) que ya existe y que estos specs ni mencionan.

Leyenda: ✅ hecho · ⚠️ parcial · ❌ no construido.

---

## Resumen de cobertura

| Pantalla | Cobertura | Nota |
|---|---|---|
| **IA Insights** | ✅ ~90% | Copilot text-to-SQL (Fase 11) |
| **Finanzas** | motor ✅ ~90% · **pantalla diseñada ~55%** | 7 KPIs/diagnostics/snapshots listos; falta el layout de 6 niveles |
| **Home** | ⚠️ ~45% | Dashboard real; falta hero, cobros netos, últimos movimientos, tarea de mañana |
| **Productos** | ⚠️ ~15% | CRUD + receta 1 nivel + margen; falta toda la inteligencia |
| **Reportes** | ❌ ~5% | = Fase 10 (Reportes+WhatsApp+Contador), pendiente |
| **Clientes / CRM** | ❌ 0% | = Fase 12 (CRM), pendiente |

---

## 1. HOME (7 niveles — doc solo texto, sin mockups)

| Nivel | Descripción del spec | Estado | Nota |
|---|---|---|---|
| 1 | Ganancia neta del día — número hero + mensaje contextual automático | ❌ | Tenemos "Neto" como KPI, no como hero con frase |
| 2 | 3 números (facturó/gastó/margen) + explicación en 1 línea humana | ⚠️ | KPIs sí; falta lenguaje "de cada $100, $65 son ganancia" |
| 3 | Cobros por canal (MP/tarjeta/efectivo) **con comisiones descontadas** + monto real acreditado + botón "Cargar efectivo" | ⚠️ | Tenemos "Medios de pago hoy" (mix). Falta: neteo de comisión, acreditado real, botón cargar efectivo en Home |
| 4 | Alerta del día (máx 1, IA) | ✅ | Recomendaciones IA (diagnostics del Asesor); muestra top 3, no "máx 1" |
| 5 | Progreso del mes (barra + proyección de cierre) | ✅ | Card "Proyección de cierre del mes" |
| 6 | Últimos 5 movimientos (monto/hora/categoría) | ❌ | No existe |
| 7 | Tarea para mañana (1 acción concreta + "Entendido") | ❌ | No existe |

---

## 2. FINANZAS (motor ✅, pantalla diseñada ~55% — 10 mockups)

**Motor / datos (lo que SÍ está):**
- Arquitectura 3 capas: `transactions` (crudo) → `snapshots` diarios/mensuales → `diagnostics` cacheados. ✅ (Tandas C+F).
- Los 7 KPIs gastronómicos: Prime Cost, Food Cost, Labor Cost, Margen de contribución por producto, RevPASH, Mermas, Rotación de inventario. ✅ (Tandas A–E).
- Comparativos vs período previo · Proyección de cierre (run-rate) · Diagnósticos narrados · Drill-down por producto · Filtros Hoy/Semana/Mes/Trimestre. ✅.

**Layout de pantalla diseñado en los mockups (lo que FALTA):**

| Nivel del mockup | Descripción | Estado |
|---|---|---|
| HERO | "Tu ganancia neta del período" (número grande + comparativo + "si seguís así cerrás en $X") | ❌ |
| Nivel 2 | **6 tarjetas por ÁREA con semáforo + headline + acción sugerida**: Tu dinero / Costo comida / Costo personal / Mermas / Mejores días / Proveedores (ej. "31% de cada $100 — sano" → Mantener; "Frigorífico Sur subió 18% vs inflación 4,2%" → Renegociar) | ⚠️ Tenemos KPIs con semáforo, pero como KPIs técnicos, no como 6 áreas con acción |
| Nivel 3 | **"Los 3 gastos que más cambiaron este mes"** (variance con el porqué: "Frigorífico +$47.000, aumentó 18% sobre inflación") | ❌ |
| Nivel 4a | Proyección de cierre ("Live Pacing", Square-style) | ✅ |
| Nivel 4b | **Distribución de gastos — donut** por categoría (Proveedores 47%, Sueldos 24%…), clickeable para filtrar | ❌ |
| Nivel 5 | KPIs del rubro (acordeón colapsado con los 7) | ✅ |
| Nivel 6 | **Búsqueda IA embebida** ("¿Cuánto gasté en proveedores?") + **Últimos movimientos** (modo Hoy/Semana) | ⚠️ búsqueda = Copilot aparte; últimos movimientos ❌ |
| Mejora | **Variance reporting** (esperado según recetas vs real según facturas → "-$128.000 → revisar mermas") | ❌ |
| Mejora | **Benchmarking local** (vs otros restaurantes de VCP / CAME-AHRCC) | ❌ (el doc dice "no para MVP") |
| Gráficos | **Donut** (gastos), **área** (proyección), **sparklines** (30 días junto a cada KPI) | ❌ usamos barras |

---

## 3. CLIENTES / CRM (9 niveles — doc solo texto, sin mockups) — ❌ 0%

Nada construido. La nav "Clientes" apunta a `/app/reservations` (reservas). **= Fase 12.**

| Nivel | Descripción | Estado |
|---|---|---|
| 1 | Hero con diagnóstico ("Identificaste 89 clientes, +18% vs abril, 57% recurrentes") | ❌ |
| 2 | **Captura automática** visible (desde MP / tarjeta / reserva online / delivery) vs carga manual | ❌ |
| 3 | **"Hoy podés hacer 3 cosas"** — acciones con plata en juego (contactar cliente en fuga, cumpleaños, agradecer al top) | ❌ |
| 4 | KPIs en lenguaje del dueño (identificados, volvieron, en riesgo, mejor mes) | ❌ |
| 5 | **Segmentación** (VIP / Recurrentes / Nuevos / En riesgo) + beneficio sugerido por segmento | ❌ |
| 6 | Top 5 clientes por **LTV** con % de facturación | ❌ |
| 7 | **Clientes en riesgo de fuga** con card detallada (días sin venir, LTV, dato emocional) | ❌ |
| 8 | "Cómo identificar más clientes" (canales activos/inactivos) | ❌ |
| 9 | Búsqueda + filtros + **ficha completa del cliente** (historial, productos favoritos, notas, contactar por WhatsApp) | ❌ |

Diferencial declarado: **CRM proactivo** (captura sola + segmenta sola + dice a quién contactar hoy) vs. el CRM pasivo de la competencia. Requiere captura automática desde pagos/reservas → depende de datos que ya tenemos (payments con método, reservations con datos del cliente) pero sin el modelo de Customer/LTV/segmentación.

---

## 4. PRODUCTOS (9 niveles — 11 mockups) — ⚠️ ~15%

| Elemento del mockup | Estado | Nota |
|---|---|---|
| Ficha de producto + receta + cálculo de utilidad ("Te deja $5.300, 62% margen") | ✅ | receta de 1 nivel |
| Tabla detalle (Precio / Costo / **Te deja** / Vendidos / **Estado**) | ⚠️ | performance por producto sin columnas "Te deja/Estado" |
| **5 categorías de menu engineering** con plata en juego: Funciona · Oportunidades ("empujá estos") · Estables ("tu base") · Revisar ("están mal") · No vendidos ("nadie los pidió, sacá tras 60 días") | ❌ | |
| **Top 3 platos que más plata dejan** + sparklines de 12 semanas | ❌ | |
| **Precios vs inflación**: platos rezagados, "último aumento hace 89 días", "debería estar en $9.500", "perdés $1.000/venta", [Simular] [Aplicar] | ❌ | |
| **Simulador de cambio de precio basado en histórico real** ("tus 2 cambios anteriores: +12% produjo -5% ventas") — NO inventa elasticidad | ❌ | |
| **Asesinos de margen** (platos que venden bien pero dejan <45% vs sano 58%) | ❌ | |
| **Cronograma de rotación por día** (heatmap Lun–Dom por plato + insights: "los lunes no se vende pizza") | ❌ | |
| **Ficha con recetas anidadas** (ingredientes directos + sub-recetas: salsa, papas, aderezo) + histórico de costos | ⚠️ | receta 1 nivel, sin anidar |
| **Recetas madre** (sección aparte): preparaciones base; cambiar el precio de un insumo actualiza todos los platos que la usan | ❌ | |
| **Carga de carta**: foto con IA / subir Excel mapeado / "que lo hagamos nosotros"; costo sugerido al crear un plato | ❌ | carga manual básica |

Reglas del spec: siempre en pesos (no %), cada plato con estado accionable, simulación con datos reales, inflación como contexto obligatorio, recetas anidadas para propagación de costos.

---

## 5. IA INSIGHTS — ✅ ~90%

Búsqueda en lenguaje natural ("Preguntá lo que necesites… ¿Cuánto gasté en proveedores?") → ✅ el **Copilot** (text-to-SQL con guardrails, Fase 11, nav "IA Insights"). El Asesor proactivo alimenta los diagnostics. Falta: exponer los insights con la UX de "acciones sugeridas" dentro de cada pantalla.

---

## 6. REPORTES (3 bloques — 6 mockups) — ❌ ~5%

Existe `/app/analytics` (ventas, mix de pagos, performance por producto) como materia prima, pero la pantalla diseñada no está. **= Fase 10 (Reportes + WhatsApp + Contador), trabada por decidir proveedor de WhatsApp.**

**Bloque 1 — Biblioteca por destinatario (tabs):**
- *Para vos (dueño):* ¿Cómo me fue este mes? · Resumen semanal (30s, WhatsApp) · ¿Cómo va la temporada? (comparativo, VCP) · Cierre del día (al cerrar caja, WhatsApp). ❌
- *Para el contador:* Resumen mensual **formato AFIP con IVA discriminado** · Listado de movimientos · Detalle de anulaciones · **Comprobantes emitidos**. ❌ (ligado a AFIP, tampoco construido)
- *Para socios/inversores:* Resumen ejecutivo 1 página (PDF premium) · Estado financiero trimestral (P&L completo). ❌
- *Uso interno:* Análisis de carta · Análisis de proveedores (precios vs inflación) · Reporte de mermas · Preparación de temporada VCP. ❌

**Bloque 2 — Envíos automáticos programados:** Resumen semanal → WhatsApp lunes 9am · Cierre mensual → email día 1 · Para el contador → email día 15 · Temporada VCP. ❌
**Bloque 3 — Historial de descargas** (archivo, fecha, tamaño, descargar/copiar link). ❌

Diferenciales declarados: múltiples destinatarios automáticos, resumen semanal por WhatsApp (ningún competidor lo hace), reporte ejecutivo de 1 página.

---

## Documentos de negocio (2 `.xlsx`) — no son features

- **Wellnod PricingyCostos.xlsx:** modelo de negocio — planes **Básico / Pro** (gating de features), precios ARS/USD, comparativa competitiva (Fudo, Mr. Comanda, Ganapán), márgenes, costos hosting+IA (Supabase+Vercel+Claude API, ~95 llamadas/mes/restaurante, 70% caché), CAC/LTV, encuadre legal **Monotributo vs SAS**. **Nota de producto:** el **sistema de planes/suscripción/billing NO está construido** (no hay gating ni cobro; la tarjeta "Plan Pro" del dashboard era mock y se removió). Ojo: el stack real es FastAPI+Postgres en Railway, no Supabase/Vercel como asume la planilla de costos.
- **base_datos_villa_carlos_paz.xlsx:** pipeline de ventas — ~33 hoteles/restaurantes/cafés de Carlos Paz con estado de contacto. Es el CRM comercial / GTM propio, no una feature.

---

## Sugerencia de troceo en planes PRP (próximos pasos)

1. **Finanzas v2 — layout completo** (hero ganancia + 6 áreas con acción + "3 gastos que más cambiaron" + donut de gastos + sparklines + últimos movimientos). El motor ya está; es mayormente frontend + 1-2 endpoints (variance, distribución de gastos). *Mayor ROI: convierte lo ya construido en la pantalla diseñada.*
2. **Home v2** (hero de ganancia neta + cobros netos de comisión + últimos movimientos + tarea de mañana). Reusa datos existentes.
3. **Productos v2** (menu engineering 5 categorías + margen "Te deja/Estado" + precios vs inflación + recetas anidadas/madre). Grande: nuevo dominio de recetas multinivel + histórico de precios.
4. **Reportes / Fase 10** (biblioteca por destinatario + PDF/Excel + WhatsApp + export contador). Depende de decidir proveedor de WhatsApp + avanza junto con AFIP para el bloque "contador/comprobantes".
5. **Clientes / CRM / Fase 12** (Customer + captura automática desde payments/reservations + LTV + segmentación + acciones). Nuevo dominio completo.

Prioridad por esfuerzo/impacto: **1 (Finanzas v2) y 2 (Home v2)** son los de mejor relación — aprovechan el motor ya hecho. 3/4/5 son features nuevas grandes.
