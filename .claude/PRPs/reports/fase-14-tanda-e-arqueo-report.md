# Implementation Report: Fase 14 — Tanda E (parte 1: caja / arqueo Z)

Subsistema de **cierre de caja / arqueo Z** (el dolor crítico del cajero):
apertura con fondo, esperado-vs-contado por medio de pago, cierre de turno con
diferencia. Autocontenido — agregado nuevo `CashSession`, sin tocar los flujos de
plata existentes (el reembolso/propina van en la parte 2).

## Cambios

**Backend (Clean Arch + RLS)**
- `domain/cashier/`: `CashSessionStatus`; `CashSession` (open con fondo, `close`
  registra los conteos); `CashCount` (esperado vs contado, `difference_amount`
  **int con signo** — el faltante es negativo, fuera de `Money` que es no-negativo).
- `application/cashier/`: `OpenCashSession` (una caja abierta a la vez),
  `GetCurrentCashReport` (arqueo en vivo), `CloseCashSession`. El esperado por
  medio = Σ inflows CONFIRMED en la ventana de la sesión; **CASH suma el fondo**.
- `payment_repo.confirmed_inflows_by_method(tenant, since, until)` (nuevo, agregado).
- Migración `0013`: `cash_sessions` + `cash_counts` con FORCE RLS + policy
  `tenant_isolation` (mirror de 0010). Aplicada al dev DB, up/down OK.
- Endpoints `POST /cashier/session/open`, `GET /cashier/session/current`,
  `POST /cashier/session/{id}/close` (roles CASHIER/MANAGER/OWNER). Excepciones
  `CashSessionNotFound`/`AlreadyOpen`/`AlreadyClosed` registradas.

**Frontend**
- `cash-api.ts` + registro DI (context/provider/test-utils); hooks `use-cash.ts`.
- `cash-session-page.tsx`: abrir (fondo) · arqueo en vivo (esperado por medio) ·
  cerrar (contado por medio) → resultado con diferencias coloreadas. Ruta
  `/app/caja` + nav "Caja" (Calculator).

## Decisiones / límites
- **Ventana temporal** para el esperado (no se linkea `cash_session_id` a cada
  pago) — más simple, sin tocar `RegisterPayment`. Limitación: un pago MP
  confirmado por webhook pero creado antes de abrir la caja podría no entrar
  (los CASH, que son lo crítico del arqueo, son inmediatos → OK).
- Una sola caja abierta por tenant a la vez.

## Validación
| Nivel | Resultado |
|---|---|
| Backend ruff + mypy | ✅ limpio |
| Backend pytest | ✅ suite completa verde (+3 unit caja, +3 e2e arqueo) |
| Migración 0013 up/down | ✅ |
| Frontend eslint | ✅ |
| Frontend vitest | ✅ 101 verdes (+3 cash-api) |
| Frontend build real (`tsc -b && vite build`) | ✅ |

## Pendiente (Tanda E parte 2)
Anular/**reembolsar** pago (revertir `sale_facts`/stock idempotente) + **reabrir**
orden + **propina** + recibo no fiscal (reusa `lib/ticket.ts` de Tanda F). Es la
parte que toca plata existente → conviene `/compact` antes.
