# Plan: App Mobile (Flutter) — Fase 1: Piso + Comanda + Modo Contingencia

## Summary
Sobre la fundación de F0, entregar el **corazón del mozo**: plano de salón en vivo, tomar/editar/anular comanda y marchar a cocina — todo **resistente a cortes de luz/internet** (cola local + sync idempotente al reconectar) y con **impresión de la comanda por Bluetooth ESC/POS** como plan B cuando no hay red/KDS. Reusa los endpoints ya existentes (idempotencia por UUID de cliente, batch, SSE). **KDS, cobro y factura quedan fuera** (F2/F3).

## User Story
Como **mozo**, quiero **tomar y editar comandas desde el teléfono y marcharlas**, incluso **si se cae la luz o el internet**, para que **el servicio no se frene y todo se sincronice solo al volver la conexión** (y la cocina reciba el ticket impreso mientras tanto).

## Problem → Solution
El mozo hoy opera en la web (lenta en mobile, se corta ante caídas de red). → **App nativa con captura optimista + cola de contingencia offline (drift/SQLite) + impresión ESC/POS por Bluetooth**, sobre los endpoints idempotentes que el backend ya tiene.

## Metadata
- **Complexity**: **XL** (4 tandas; se puede dividir la implementación)
- **Source PRD**: `.claude/PRPs/prds/mobile-app.prd.md`
- **PRD Phase**: Fase 1 — Piso + Comanda + Contingencia
- **Depends on**: Fase 0 (fundaciones, ya en `feat/mobile-fase-0`)
- **Estimated Files**: ~30 nuevos bajo `mobile/` + codegen; **0** fuera de `mobile/` (ver decisión de modificadores)

---

## UX Design

### Before
F0 dejó login → Home + tabs placeholder. El mozo no puede operar todavía.

### After
```
Piso (tab)                         Comanda (al tocar una mesa)
┌───────────────────────────┐      ┌───────────────────────────┐
│ ⚠ Requieren atención      │      │ Mesa 5 · 4p · 12′         │
│ [M3 a servir][M7 a cobrar]│      │ ── Buscar producto ────── │
│ Chips: Todas|Servir|Cobrar│      │ [grilla productos +/−]    │
│ ▸ Salón (5)               │      │ ── Comanda ────────────   │
│  [M1][M2][M3 ámbar]       │ ───▶ │ 2× Pizza                  │
│  [M4][M5 verde]           │      │ 1× Agua        (PENDING±✕)│
│ ▸ Terraza (3)             │      │ Total (server) $X         │
│ ● offline: 2 en cola ↻    │      │ [ Marchar (3) ]  🖨        │
└───────────────────────────┘      └───────────────────────────┘
```

### Interaction Changes
| Touchpoint | Web (hoy) | Mobile (F1) | Notas |
|---|---|---|---|
| Plano | grilla de cards por sector | idem, nativo | estado derivado, timer, chips |
| En vivo | SSE + poll 10s | idem (SSE 2-pasos + poll) | señal→refetch |
| Comanda | optimista, UUID en body | idem + **cola offline** | web NO tiene cola; mobile sí |
| Ante corte | se frena | **sigue + imprime + sync** | plan B cocina = ESC/POS |
| Cocina | KDS/navegador | **ESC/POS Bluetooth** | port de `ticket.ts` |

---

## Mandatory Reading

### Backend (contratos)
| Prioridad | Archivo | Líneas | Por qué |
|---|---|---|---|
| P0 | `backend/app/presentation/api/v1/orders.py` | 88-359 | create/items/batch/send/transfer/merge/advance — el contrato de la comanda |
| P0 | `backend/app/application/order/use_cases.py` | 68-71, 144-160, 202-297 | **idempotencia por UUID de cliente** (replay=no-op), batch, eventos SSE |
| P0 | `backend/app/presentation/api/v1/floor.py` | 69-119 | `GET /floor`, abrir sesión, pedir cuenta, pax |
| P0 | `backend/app/application/floor/use_cases.py` | 39-84 | read-model del piso (occupancy + estado derivado) |
| P0 | `backend/app/domain/table_session/status.py` | 35-70 | precedencia del estado derivado (TO_SERVE>TO_CHARGE>IN_KITCHEN>SERVED>OPEN) |
| P0 | `backend/app/presentation/api/v1/realtime.py` | 24-90 | **SSE en 2 pasos**: `POST /realtime/token` → `GET /realtime/{floor,kds}/stream?token=` |
| P1 | `backend/app/domain/order/entities.py` | 25-56, 126-138, 213-251 | OrderItem, `march()`, `total()`, roll-up de status |
| P1 | `backend/app/domain/order/value_objects.py` | 7-60 | `ItemStatus`, `Station`, `SelectedOption`, `OrderSource` |
| P1 | `backend/app/presentation/api/v1/products.py` | 94-101, 239-247 | `GET /products`, `GET /products/{id}/modifiers` |
| P1 | `backend/app/domain/product/modifiers.py` | 62-94 | `select_options` (precio server-side) — para modificadores (diferido) |
| P1 | `backend/app/presentation/schemas/` | `orders.py`, `floor.py`, `products.py`, `modifiers.py` | DTOs de respuesta que consume el cliente Dart |

### Frontend (UX a espejar)
| Prioridad | Archivo | Por qué |
|---|---|---|
| P0 | `frontend/src/features/orders/order-page.tsx` | Estructura de la comanda (grilla→carrito→marchar→mover/unir) |
| P0 | `frontend/src/hooks/use-orders.ts` | **Optimistic updates + idempotencia** (el patrón exacto a portar) |
| P0 | `frontend/src/lib/ids.ts` | `crypto.randomUUID()` → `id` de cliente (idempotente) |
| P0 | `frontend/src/features/floor/floor-page.tsx` | Grilla por sector, chips, tira de atención, `TableCard` |
| P0 | `frontend/src/lib/floor-session.ts`, `floor-filter.ts` | `floorView` (estado/timer/pax derivados) + chips |
| P0 | `frontend/src/hooks/use-floor.ts`, `use-realtime.ts`, `src/api/realtime-api.ts` | SSE 2-pasos + poll de fallback |
| P0 | `frontend/src/lib/ticket.ts` | **Referencia canónica** para el ticket ESC/POS (agrupar por `station`, `qty×`, nota) |
| P1 | `frontend/src/features/orders/product-grid.tsx`, `src/lib/product-usage.ts` | Grilla + ranking por uso (localStorage) |
| P1 | `frontend/src/api/orders-api.ts` | `addItemsBatch(...)` — el endpoint idempotente "used by the offline queue" |
| P1 | `frontend/src/i18n/locales/es/{floor,orders}.ts` | Claves a portar |

## External Documentation
| Topic | Package | Takeaway |
|---|---|---|
| Codegen OpenAPI→Dart | `swagger_parser` (dev) | Genera modelos de order/floor/product desde `/openapi.json` (OpenAPI 3.1) |
| Cola offline / DB local | `drift` + `sqlite3_flutter_libs` | Tabla de operaciones pendientes (transaccional) |
| Conectividad | `connectivity_plus` | Detectar online/offline para disparar el flush |
| UUID | `uuid` | `Uuid().v4()` = el `id` de cliente idempotente |
| SSE | streamed `dio` (ResponseType.stream) o `flutter_client_sse` | No hay EventSource nativo; parsear `event:`/`data:` |
| ESC/POS | `esc_pos_utils_plus` + `print_bluetooth_thermal` (o `flutter_blue_plus`) | Encodear el ticket a bytes + imprimir por BT |

---

## Patterns to Mirror

### CLIENT_UUID_IDEMPOTENCY
// SOURCE: frontend/src/lib/ids.ts + backend/app/application/order/use_cases.py:68-71
```ts
ordersApi.create(tableId, newId())   // id de cliente; replay con el mismo id = no-op en server
```
→ Dart: `final id = const Uuid().v4();` generado ANTES de encolar; se reusa idéntico en cada reintento. Es la base del modo contingencia (no hay header Idempotency-Key para órdenes; el id va en el body).

### OPTIMISTIC_ADD
// SOURCE: frontend/src/hooks/use-orders.ts:54-93
```ts
onMutate: inserta OrderItem optimista con el id FINAL del cliente + ajusta total; onError: rollback; onSettled: invalida ["order", id]
```
→ Dart/Riverpod: el `OrderNotifier` aplica el ítem localmente con el UUID, encola la op, y reconcilia con el refetch (mismo id → sin flicker ni duplicado).

### FLOOR_DERIVED_VIEW
// SOURCE: frontend/src/lib/floor-session.ts:49-84
```ts
floorView(table): prefiere table.session.state (OPEN/IN_KITCHEN/TO_SERVE/SERVED/TO_CHARGE) y cae a active_order.status; attention = TO_SERVE||TO_CHARGE
```
→ Dart: función pura `floorView(FloorTable)` que alimenta color/timer/chip de forma consistente.

### SSE_TWO_STEP
// SOURCE: frontend/src/hooks/use-realtime.ts + backend realtime.py:24-90
```
POST /realtime/token (Bearer) -> {token}     // EventSource no manda Authorization
GET  /realtime/floor/stream?token=...         // event: floor.changed -> el cliente REFETCHEA
```
→ Dart: un `SseClient` sobre stream HTTP que, ante `floor.changed`, invalida el provider del piso (que refetchea). Poll de fallback cada 10s (Timer). Reconecta a los 3s.

### KITCHEN_TICKET (para ESC/POS)
// SOURCE: frontend/src/lib/ticket.ts:51-81
```ts
ticketHtml: agrupa por station (COCINA/BARRA), imprime `qty× name`, la nota (`› ...`)
```
→ Dart: `escposTicket(order, tableLabel)` que agrupa por `station`, formatea `qty× name`, la `note`, **y agrega `selected_options`** (gap del web) → bytes ESC/POS.

---

## Files to Change (todo bajo `mobile/`)

| Área | Archivos (nuevos) | Acción |
|---|---|---|
| Codegen | `lib/api/generated/**` (order, floor, table, sector, product, modifiers) | swagger_parser desde `/openapi.json` |
| Repos/clients | `lib/features/floor/floor_repository.dart`, `lib/features/order/order_repository.dart`, `lib/features/order/product_repository.dart` | usan `apiDio` (F0) + modelos generados |
| Realtime | `lib/data/realtime/sse_client.dart`, `realtime_token.dart`, `realtime_providers.dart` | SSE 2-pasos + reconexión |
| Piso | `lib/features/floor/floor_page.dart`, `table_card.dart`, `floor_view.dart`, `floor_filter.dart`, `floor_providers.dart` | grilla por sector, chips, atención, estado derivado |
| Comanda | `lib/features/order/order_page.dart`, `product_grid.dart`, `cart_list.dart`, `order_providers.dart`, `product_usage.dart` | captura optimista + marchar + mover/unir |
| Contingencia | `lib/data/offline/queue_db.dart` (drift), `queue_op.dart`, `sync_service.dart`, `connectivity.dart`, `sync_indicator.dart` | cola + reintento idempotente + estado |
| Impresión | `lib/data/printing/escpos_ticket.dart`, `bluetooth_printer.dart`, `printer_providers.dart`, `lib/features/settings/printer_page.dart` | encoder + pairing + print-on-send |
| Shell | editar `lib/features/shell/app_scaffold.dart` (F0) | reemplazar los placeholders del mozo por Piso/Comanda reales |
| i18n | editar `lib/l10n/strings.dart` (F0) | claves floor/orders |

## NOT Building
- **KDS** (pantalla de cocina) → **Fase 2**.
- **Cobro / split / propina / arqueo / factura AFIP** → **Fase 3**.
- **Selección de modificadores desde el mozo** → diferido: requiere extender la schema de presentación del batch (`schemas/orders.py` `BatchOrderItem` no expone `selected_options`). **F1 mantiene paridad con la web** (el mozo agrega productos sin modificadores; la comanda solo *muestra* los `selected_options` que llegan por Carta QR). Si se quiere, es un cambio de backend acotado aparte.
- Sección de cliente CRM en la comanda (`OrderCustomer`).
- Push / cámara-QR (fases posteriores).

---

## Step-by-Step Tasks (por tandas)

### Tanda 1 — Codegen + Piso en vivo

**T1.1 Codegen OpenAPI→Dart**
- **ACTION**: configurar `swagger_parser` (dev dep) y generar modelos de `orders`, `floor`, `tables`, `sectors`, `products`, `modifiers`.
- **IMPLEMENT**: `curl http://localhost:8000/openapi.json > tool/openapi.json`; config apuntando a `lib/api/generated/`; `dart run swagger_parser`. Commitear lo generado.
- **GOTCHA**: OpenAPI **3.1** — `swagger_parser` lo soporta; si algo falla, bajar el schema a 3.0 antes de generar.
- **VALIDATE**: `flutter analyze` limpio incluyendo `generated/`.

**T1.2 SSE 2-pasos**
- **ACTION**: `sse_client.dart` + `realtime_token.dart`.
- **IMPLEMENT**: `POST /realtime/token` (Bearer, via `apiDio`) → token; abrir `GET /realtime/floor/stream?token=` como stream HTTP, parsear líneas `event:`/`data:`; ante `floor.changed` invalidar el provider del piso. Reconectar a los 3s con token fresco; ignorar heartbeat `: ping`.
- **MIRROR**: `SSE_TWO_STEP`.
- **VALIDATE**: test unit del parser de eventos SSE (líneas → evento).

**T1.3 Floor repo + providers + estado derivado**
- **ACTION**: `floor_repository.dart` (`GET /floor`, `GET /sectors`), `floor_view.dart` (pura), `floor_providers.dart`.
- **IMPLEMENT**: provider del piso = fetch inicial + **poll fallback 10s** (Timer) + invalidación por SSE. `floorView(table)` deriva estado/timer/pax/attention.
- **MIRROR**: `FLOOR_DERIVED_VIEW`.
- **GOTCHA**: el estado NO viene del server como enum de UI; se deriva de `session.state` con fallback a `active_order.status`.
- **VALIDATE**: test de `floorView` (precedencia de estados, fallback).

**T1.4 Floor page**
- **ACTION**: `floor_page.dart`, `table_card.dart`, `floor_filter.dart`.
- **IMPLEMENT**: grilla de cards agrupadas por sector (colapsable, punto de color), tira "Requieren atención" (TO_SERVE/TO_CHARGE), chips (todas/servir/cobrar/mías/libres), `TableCard` (número/pax/badge/total/mozo/timer/"Pedir cuenta"). Abrir mesa: si hay `active_order` → navegar a la comanda; si libre → crear orden idempotente y navegar. `POST .../bill` para pedir cuenta.
- **MIRROR**: `floor-page.tsx`, `floor-filter.ts`.
- **VALIDATE**: correr contra prod/local; el piso refleja mesas reales y refetchea ante cambios.

### Tanda 2 — Comanda (captura)

**T2.1 Productos**
- **ACTION**: `product_repository.dart` (`GET /products`), `product_usage.dart` (ranking por uso, `shared_preferences`), `product_grid.dart`.
- **IMPLEMENT**: grilla con buscador + ranking por uso (más usados primero) + stepper de cantidad; tap = agregar.
- **MIRROR**: `product-grid.tsx`, `product-usage.ts`.
- **VALIDATE**: la grilla lista productos reales; el orden respeta el uso guardado.

**T2.2 Order repo + captura optimista**
- **ACTION**: `order_repository.dart` (create/addItem/remove/setQty/send/transfer/merge), `order_providers.dart` (`OrderNotifier`).
- **IMPLEMENT**: cada mutación genera/usa el **UUID de cliente**; aplica el cambio **optimista** en el estado local y reconcilia con el refetch. Editar/anular solo si el ítem está PENDING. `total` se muestra del server (no se calcula en el cliente).
- **MIRROR**: `OPTIMISTIC_ADD`, `CLIENT_UUID_IDEMPOTENCY`.
- **GOTCHA**: el server valida y congela `unit_price`; el cliente nunca manda precio.
- **VALIDATE**: agregar/editar/anular/marchar contra el backend; sin duplicados al reconciliar.

**T2.3 Order page + marchar + mover/unir**
- **ACTION**: `order_page.dart`, `cart_list.dart`.
- **IMPLEMENT**: carrito line-based (`qty× name`, nota, `selected_options` si vienen; ±/✕ solo en PENDING), botón **Marchar** (`POST /orders/{id}/send`, deshabilitado si 0 pendientes), sección mover/unir (dropdowns que leen el piso en vivo → `transfer`/`merge`).
- **MIRROR**: `order-page.tsx`.
- **VALIDATE**: marchar envía a cocina (aparece en el KDS web); mover/unir funciona.

### Tanda 3 — Modo contingencia (offline)

**T3.1 Cola local (drift)**
- **ACTION**: `queue_db.dart` (drift), `queue_op.dart`.
- **IMPLEMENT**: tabla de ops pendientes (tipo: createOrder / addItemsBatch / send / transfer / merge; payload JSON con los UUIDs de cliente; estado: pending/failed; timestamps). Toda mutación de comanda **encola** + aplica optimista local.
- **VALIDATE**: test: encolar/leer/marcar-sincronizada.

**T3.2 Conectividad + sync**
- **ACTION**: `connectivity.dart` (`connectivity_plus`), `sync_service.dart`, `sync_indicator.dart`.
- **IMPLEMENT**: al recuperar red (o periódicamente) drenar la cola en orden, usando `POST /orders/{id}/items/batch` (idempotente) y los endpoints con los UUIDs; el server dedup por id → reintentos seguros. Indicador de estado ("N en cola / sincronizando / al día"). El **server es la verdad**: tras drenar, refetch reconcilia.
- **MIRROR**: `addItemsBatch` (`orders-api.ts`), `CLIENT_UUID_IDEMPOTENCY`.
- **GOTCHA**: mientras no hay red, un KDS digital en otra tablet NO ve la comanda hasta el sync — por eso Tanda 4 (impresión local) es el plan B de cocina.
- **VALIDATE**: con el wifi apagado, tomar comanda → queda en cola → al reconectar aparece en el backend **sin duplicar**.

### Tanda 4 — Impresión ESC/POS por Bluetooth

**T4.1 Encoder del ticket**
- **ACTION**: `escpos_ticket.dart`.
- **IMPLEMENT**: portar la lógica de `ticket.ts` a comandos ESC/POS: agrupar por `station` (COCINA/BARRA), `qty× name`, nota, **y `selected_options`** (que el web hoy no imprime), corte de papel. Ancho angosto (58/80mm).
- **MIRROR**: `KITCHEN_TICKET` (`ticket.ts:51-81`).
- **VALIDATE**: test del encoder (bytes esperados para una comanda de ejemplo).

**T4.2 Impresora BT + settings**
- **ACTION**: `bluetooth_printer.dart`, `printer_providers.dart`, `printer_page.dart`.
- **IMPLEMENT**: descubrir/emparejar impresora ESC/POS (paquete BT), guardar la elegida; imprimir al **marchar** (y reimprimir manual). Detrás de un port (`Printer`) para tolerar variedad de hardware.
- **GOTCHA**: variedad de impresoras/permports BT (iOS pide permisos); probar con una impresora real temprano.
- **VALIDATE**: imprimir una comanda real en una térmica; imprime aunque no haya red.

---

## Testing Strategy
| Test | Qué valida | Tanda |
|---|---|---|
| `floorView` | estado derivado + fallback + attention | 1 |
| SSE parser | líneas `event:`/`data:` → evento | 1 |
| OrderNotifier optimista | add/edit/remove con UUID, reconciliación sin duplicado | 2 |
| queue_db | encolar/leer/marcar sincronizada | 3 |
| sync_service | drenar en orden, reintento idempotente, server-authoritative | 3 |
| escpos_ticket | bytes del ticket (agrupado por estación + opciones) | 4 |

### Edge Cases
- [ ] Tomar comanda offline → cola → sync al reconectar (sin duplicar)
- [ ] Reintento de una op ya aplicada → no-op (mismo UUID)
- [ ] Editar/anular un ítem ya marchado → bloqueado (no PENDING)
- [ ] SSE cae → reconecta a los 3s; poll cubre el hueco
- [ ] Impresora desconectada → error claro + reintento, la comanda igual quedó registrada

## Validation Commands
```bash
cd mobile
flutter analyze                         # 0 issues (incl. generated/)
flutter test                            # unit tests de las 4 tandas
dart run swagger_parser                 # regenerar modelos si cambió el OpenAPI
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1   # Android
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1  # iOS sim
```
Manual: abrir mesa → tomar comanda → marchar (verificar en KDS web) → apagar wifi → tomar otra → reconectar → aparece sin duplicar → imprimir ticket.

## Acceptance Criteria
- [ ] Plano de salón en vivo (SSE + poll), estados/timers correctos, abrir mesa
- [ ] Tomar/editar/anular comanda (optimista, UUID) y marchar a cocina
- [ ] Mover/unir mesa
- [ ] Modo contingencia: tomar comanda sin red → sync idempotente al reconectar (0 duplicados/perdidos)
- [ ] Impresión ESC/POS por Bluetooth de la comanda (incluye modificadores)
- [ ] `flutter analyze` 0 issues, `flutter test` verde
- [ ] Cero cambios fuera de `mobile/` (modificadores del mozo diferidos)

## Risks
| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| SSE en Dart (sin EventSource nativo) | M | M | Implementar sobre stream HTTP + reconexión; poll de fallback cubre huecos |
| Sync offline con conflictos | M | Alto | Server-authoritative (refetch) + idempotencia por UUID ya existente |
| Variedad de impresoras ESC/POS | M | M | Detrás de un port `Printer`; probar hardware real temprano |
| Codegen OpenAPI 3.1 | B | M | `swagger_parser`; fallback bajar a 3.0 |
| Modificadores del mozo (paridad) | B | B | Diferido; F1 = paridad web (sin modificadores del mozo) |

## Notes
- **Net-new real**: la web NO tiene cola offline (el `addItemsBatch` está en el cliente API pero sin UI que lo use). La app mobile es la primera en cablear la contingencia sobre los endpoints idempotentes ya existentes — de ahí el mayor valor de F1.
- **Paridad de modificadores**: hoy solo la Carta QR captura modificadores; el mozo (web y mobile) agrega productos directo. Mantener paridad evita tocar el backend en F1.
- **F0 → F1**: se reusa todo lo de F0 (auth, apiDio, ThemeData, glass, i18n, shell). El shell reemplaza los placeholders del mozo por Piso/Comanda.
- Próximo: `/prp-implement .claude/PRPs/plans/mobile-fase-1-piso-comanda.plan.md` (sugerido tanda por tanda).
