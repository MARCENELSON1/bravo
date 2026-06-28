# Implementation Report: Fase 14 — Tanda F (impresión de comanda, MVP)

Impresión de comanda **por navegador** (MVP, sin hardware): un ticket angosto y
monoespaciado, **agrupado por estación** (Cocina/Barra), que se imprime con
`window.print()`. Una impresora térmica seteada como destino del diálogo de
impresión produce el ticket físico.

## Cambios (frontend-only)
- `lib/ticket.ts`:
  - `ticketHtml(order, tableLabel, printedAt, station?)` — **puro**: arma el HTML
    del ticket agrupado por estación; `station` opcional lo limita a una. Escapa HTML.
  - `TICKET_CSS` + `printTicket(html)` — abre una ventana print-only y dispara el diálogo.
- `order-page.tsx`: botón **"Imprimir"** en la card de ítems (roles de salón, con
  ítems); resuelve el número de mesa vía `useTables` y arma el `printedAt` en el handler.

## NO incluido (follow-up)
- **Port `TicketPrinter` backend + ESC/POS por red** (impresión server→impresora):
  necesita hardware/red reales → follow-up, como anticipaba el plan ("hardware real
  es follow-up").
- Auto-impresión al marchar: se dejó manual (botón) para no depender de una
  impresora configurada.

## Validación
| Nivel | Resultado |
|---|---|
| Frontend eslint | ✅ limpio |
| Frontend vitest | ✅ 98 verdes (+4 `ticketHtml`) |
| Frontend build real (`tsc -b && vite build`) | ✅ |

> Nota: se validó con `npm run build` (gate real), no con `tsc --noEmit`. Ver
> [[feedback-frontend-build-gate]].

## Pendiente de Fase 14
Solo queda **Tanda E** (cierre de caja / arqueo Z — el subsistema más grande;
conviene `/compact` antes).
