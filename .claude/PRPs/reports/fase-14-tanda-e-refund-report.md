# Implementation Report: Fase 14 — Tanda E (parte 2a: anular/reembolsar + recibo)

La parte **segura** de la E parte 2: **anular/reembolsar** un cobro (money-only) y
**recibo no fiscal**. Sin migración, sin tocar `sale_facts`/stock (el reverso de la
venta = reabrir orden, queda como E parte 2b).

## Cambios

**Backend**
- `Payment.refund()`: CONFIRMED→REFUNDED (excepción `PaymentNotRefundable` 409 si no
  está confirmado). Money-only: el arqueo ya filtra `status=CONFIRMED`, así que un
  pago anulado deja de contar; la proyección de venta no se toca.
- Use case `RefundPayment` + endpoint `POST /payments/{payment_id}/refund`
  (CASHIER/MANAGER/OWNER) + wiring DI + registro de error.

**Frontend**
- `paymentsApi.refund` + hook `useRefundPayment` (invalida order + order-payments +
  cash-session).
- `CobroSection`: botón **"Anular"** por cada pago confirmado (muestra "anulado"
  tachado) + botón **"Recibo"** que imprime el recibo no fiscal.
- `lib/ticket.ts`: `receiptHtml(order, tableLabel, printedAt, payments)` (puro:
  ítems + total + cómo se pagó), reusa `printTicket`/`TICKET_CSS` de Tanda F.

## Validación
| Nivel | Resultado |
|---|---|
| Backend ruff + mypy | ✅ limpio |
| Backend pytest | ✅ suite completa verde (+3 unit refund, +1 e2e arqueo) |
| Frontend eslint | ✅ |
| Frontend vitest | ✅ 103 verdes (+2: refund api, receipt) |
| Frontend build real (`tsc -b && vite build`) | ✅ |

## Pendiente — SOLO queda E parte 2b (la más riesgosa)
**Reabrir orden PAID** con reverso **idempotente** de `sale_facts` + stock (el inverso
de `ProjectOrderSales`/`ConsumeRecipesForOrder`), guard si hay `Invoice` AFIP
autorizada, + **propina** (`payments.tip_amount`, migración). Toca plata/proyecciones
sobre data real → **`/compact` antes**.
