# Implementation Report: Fase 14 — Tanda D (mover / unir mesas)

Movimientos de mesa para el mozo: **transferir** una comanda a otra mesa y **unir**
dos mesas (se fusionan los ítems y se cierra la de origen). Reusa el `EventBus`
(emite `floor.changed` de ambas mesas) y respeta el ciclo por ítem de Tanda C
(cada ítem movido conserva su status/station/sent_at).

## Cambios

**Backend**
- `Order.transfer_to(table_id)` — cambia de mesa salvo PAID/CANCELLED.
- `Order.merge_from(other)` — absorbe los ítems de `other`, lo vacía y lo deja
  CANCELLED (libera su mesa). Valida estados terminales + moneda.
- Use cases `TransferOrder` (valida que la mesa destino exista) y `MergeOrders`
  (guard de auto-merge; guarda primero la fuente vaciada para no colisionar ids al
  reinsertar los ítems en el destino). Emiten `floor.changed` de ambas mesas y
  `kds.changed` por estación de los ítems movidos.
- Endpoints `POST /orders/{id}/transfer` y `POST /orders/{id}/merge` (roles de salón).
- Wiring DI `transfer_order` / `merge_orders`.

**Frontend**
- `ordersApi.transfer` / `merge`; hooks `useTransferOrder` / `useMergeOrders`
  (invalidan `order` + `floor`).
- `TableMoveSection` en la comanda (visible para roles de salón en orden activa):
  lee el plano en vivo → "Mover a mesa…" (libres) y "Unir otra mesa acá…" (otras
  ocupadas).

## Validación

| Nivel | Resultado |
|---|---|
| Backend ruff + mypy | ✅ limpio |
| Backend pytest | ✅ suite completa verde (+5 unit, +1 e2e transfer/merge) |
| Frontend tsc + eslint | ✅ limpio |
| Frontend vitest | ✅ 94 verdes (+2 transfer/merge) |
| Frontend build | ✅ |

## Pendiente de Fase 14
Tandas **E** (cierre de caja/arqueo Z — el más grande) y **F** (impresión térmica, MVP).
