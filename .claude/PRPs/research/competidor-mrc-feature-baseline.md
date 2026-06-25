# Baseline de funcionalidad — MRC / Mr Comanda (benchmark competitivo)

> Objetivo: usar el set de features de **MRC** (incumbente maduro: 25+ años, 8.000+ licencias, AR + Chile,
> freemium) como **línea base de paridad operativa** para NÚCLEO, separando lo que es *table-stakes* (hay que
> igualar para ser creíble) de lo *diferenciador* (donde NÚCLEO ya gana). **No se copia** código/UI/marca/assets —
> sólo se benchmarkea funcionalidad (legítimo y normal en competencia).

## Cómo capturar su funcionalidad (yo no puedo ver videos)
1. **Sitio/help/feature pages** — `mrcomanda.com` (hoy con cert SSL roto), `regitronic`, `sistemaparagastronomia`.
   Cuando funcione, lo leo y extraigo features. Mientras tanto, copiás el texto de las páginas y lo pego acá.
2. **Demos de YouTube** (canal `@mktmrc`) — YouTube es JS, WebFetch no lee la lista. **Vos** mirás la demo y:
   - pegás la **transcripción** (YouTube → ⋯ → "Mostrar transcripción"), o
   - me contás el flujo en 3–4 bullets por video.
   Yo lo convierto en features estructuradas y las agrego a la matriz de abajo.
3. **MRC Free** — registrate en la versión gratis, recorré las pantallas, sacá screenshots / describí flujos.
4. **Reviews / Facebook / foros** — qué piden y qué se quejan los usuarios = pistas de gaps y de lo que valoran.

## Matriz de paridad (semilla — completar con los demos)
Leyenda: ✅ tiene · 🟡 parcial · ❌ falta.

| Módulo MRC | MRC | NÚCLEO | Estado | Nota |
|---|---|---|---|---|
| Comandas mozo→cocina | ✅ | ✅ (Fase 2) | ✅ | |
| KDS (pantalla cocina) | ✅ | ✅ (Fase 2) | ✅ | |
| **Impresión de comandas térmicas / ruteo a impresoras** (hasta 12) | ✅ | ❌ | **GAP** | NÚCLEO es web/KDS; sin ruteo a impresoras |
| **Llamador / fila (fast food)** | ✅ | ❌ | **GAP** | display de pedido listo |
| Cobro / POS | ✅ | ✅ (Fase 3, Manual+MP) | ✅ | |
| Factura electrónica AFIP | ✅ | ✅ (Fase 4, WSFEv1/CAE) | ✅ | **no es diferencial** |
| Stock / insumos | ✅ | ✅ (Fase 6) | ✅ | |
| Mermas | ✅ | ✅ (Fase 6, WASTE) | ✅ | |
| **Acuerdos con proveedor** (multi-prov, presentación, precio) + órdenes de compra | ✅ | 🟡 | **GAP** | NÚCLEO: 1 proveedor simple, sin OC |
| **Consumo de personal** (registrar lo que come el staff) | ✅ | ❌ | **GAP** | |
| Food cost / receta | 🟡 (precios proveedor) | ✅ (Fase 6, food cost+margen) | **NÚCLEO+** | acá estás MÁS arriba |
| RRHH / personal | ✅ | 🟡 (fichaje horas, Fase 5) | **GAP** | sin liquidación/payroll |
| **Cierre de caja diario (Z)** — contado vs esperado por medio | ✅ | ❌ | **GAP fuerte** | ritual diario, alto uso |
| Contabilidad / export contador | ✅ | 🟡 (Fase 10 pendiente) | **GAP** | Excel + IVA discriminado = Fase 10 |
| Reportes: ranking productos | ✅ | ✅ (Fase 8 product perf) | ✅ | |
| Reportes: ticket promedio | ✅ | ✅ (Fase 9) | ✅ | |
| Reportes: cubiertos promedio | ✅ | 🟡 | 🟡 | NÚCLEO: covers en reservas, no por comanda |
| **Multi-sucursal / cadenas / franquicias** | ✅ | ❌ | **GAP** | NÚCLEO multi-tenant, sin consolidado por dueño |
| **Delivery / integración apps de pedido** (PedidosYa/Rappi) | ✅ (apps) | ❌ | **GAP** | |
| Reservas / no-shows | ❓ | ✅ (Fase 7) | **NÚCLEO+?** | confirmar si MRC tiene |
| **Asesor financiero en pesos** (margen/break-even/food-labor-prime cost, insights) | ❌ | ✅ (Fase 9) | **NÚCLEO++** | LO TUYO |
| **Copiloto conversacional** (preguntás en español) | ❌ | ✅ (Fase 11) | **NÚCLEO++** | LO TUYO |
| **Repricing inteligente** (precio sugerido a margen objetivo) | ❌ | ❌ (idea) | **OPORTUNIDAD** | wedge AR (inflación) |
| Multi-país / pagos Chile | ✅ | ❌ | — | si pensás expandir |
| Freemium (MRC Free) | ✅ | ❌ | — | decisión de pricing, no feature |

## Lectura estratégica
- **Tu wedge se confirma:** MRC (como Fudo/Maxirest) es **fortísimo en captura, cero en inteligencia**. El asesor +
  copiloto + (futuro) repricing **no los tiene nadie**. Liderá con eso; **no intentes ganarles en POS** (25 años +
  8.000 licencias + freemium = inercia enorme).
- **Gaps table-stakes a cerrar** (para que un dueño "no sienta que le falta algo" al cambiarse):
  1. **Cierre de caja diario (Z)** — ritual diario, barato, alto enganche. *(Top prioridad operativa.)*
  2. **Export contador** (= Fase 10, ya en roadmap).
  3. **Multi-sucursal / consolidado** (si apuntás a cadenas).
  4. **Delivery / apps de pedido** (si el segmento lo pide).
  5. **Impresión de comandas térmicas** (muchos locales todavía imprimen en cocina).
  6. **Órdenes de compra / multi-proveedor** (cierra el loop de stock).
- **No persigas paridad total:** elegí los gaps que tu segmento (PyME, dueño que quiere entender su plata) realmente
  necesita. Algunos (RRHH/payroll completo, multi-país) pueden no valer el esfuerzo en el MVP.

## Próximo paso sugerido
1. Mirás 3–5 demos del canal y me pasás transcripciones/notas → **completo la matriz** (sobre todo los ❓ y el
   detalle de cómo opera su comandera/cierre de caja).
2. Con la matriz cerrada, priorizamos: **diferenciación primero** (repricing) + **1–2 table-stakes** que más duelan
   (probablemente **cierre de caja** + **export contador**).
