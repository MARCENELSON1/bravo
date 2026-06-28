import type { OrderDTO, OrderItemDTO, Station } from "@/api/types-operations"
import { formatMoney } from "@/lib/money"

// Browser-printed comanda ticket (MVP, no hardware): builds a narrow,
// monospace ticket grouped by station so the kitchen and the bar each see their
// own lines. Server-side ESC/POS network printing stays a follow-up behind a
// future TicketPrinter port.

const STATION_LABEL: Record<Station, string> = {
  KITCHEN: "COCINA",
  BAR: "BARRA",
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
}

// Pure: returns the ticket body HTML. `station` limits it to one station's items
// (the kitchen/bar board's ticket); omit it to print the whole comanda grouped.
export function ticketHtml(
  order: OrderDTO,
  tableLabel: string,
  printedAt: string,
  station?: Station
): string {
  const items = station ? order.items.filter((it) => it.station === station) : order.items
  const byStation = new Map<Station, OrderItemDTO[]>()
  for (const it of items) {
    const bucket = byStation.get(it.station)
    if (bucket) bucket.push(it)
    else byStation.set(it.station, [it])
  }

  const sections = [...byStation.entries()]
    .map(([st, lines]) => {
      const rows = lines
        .map((it) => {
          const note = it.note
            ? `<div class="note">› ${escapeHtml(it.note)}</div>`
            : ""
          return `<div class="line"><span class="qty">${it.quantity}×</span> ${escapeHtml(it.name)}</div>${note}`
        })
        .join("")
      return `<div class="station">${STATION_LABEL[st]}</div>${rows}`
    })
    .join("")

  return `<div class="ticket"><div class="head">${escapeHtml(tableLabel)}</div><div class="meta">${escapeHtml(printedAt)}</div>${sections || '<div class="line">— sin ítems —</div>'}</div>`
}

export interface ReceiptPaymentLine {
  label: string
  amount: number // minor units
}

// Pure: a non-fiscal receipt (recibo) for the customer — items + total + how it
// was paid. Not an AFIP comprobante; that's the invoice flow.
export function receiptHtml(
  order: OrderDTO,
  tableLabel: string,
  printedAt: string,
  payments: ReceiptPaymentLine[]
): string {
  const lines = order.items
    .map(
      (it) =>
        `<div class="line"><span class="qty">${it.quantity}×</span> ${escapeHtml(it.name)}` +
        `<span class="amt">${formatMoney(it.unit_price_amount * it.quantity, order.currency)}</span></div>`
    )
    .join("")
  const paid = payments
    .map(
      (p) =>
        `<div class="line">${escapeHtml(p.label)}<span class="amt">${formatMoney(p.amount, order.currency)}</span></div>`
    )
    .join("")
  return (
    `<div class="ticket"><div class="head">${escapeHtml(tableLabel)}</div>` +
    `<div class="meta">RECIBO NO FISCAL · ${escapeHtml(printedAt)}</div>` +
    `${lines}` +
    `<div class="station">TOTAL<span class="amt">${formatMoney(order.total_amount, order.currency)}</span></div>` +
    `${paid}` +
    `</div>`
  )
}

export const TICKET_CSS = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: ui-monospace, "Courier New", monospace; }
  .ticket { width: 280px; padding: 8px; color: #000; }
  .head { font-size: 20px; font-weight: 700; text-align: center; }
  .meta { font-size: 11px; text-align: center; margin-bottom: 8px; }
  .station { font-weight: 700; border-top: 1px dashed #000; border-bottom: 1px dashed #000; margin: 6px 0 4px; padding: 2px 0; }
  .line { font-size: 14px; line-height: 1.4; overflow: hidden; }
  .amt { float: right; font-variant-numeric: tabular-nums; }
  .qty { font-weight: 700; }
  .note { font-size: 12px; padding-left: 14px; font-style: italic; }
  @media print { @page { margin: 4mm; } }
`

// Thin: opens a print-only window with the ticket and triggers the dialog. A
// thermal printer set as the print target produces the physical ticket.
export function printTicket(bodyHtml: string): void {
  const w = window.open("", "_blank", "width=320,height=640")
  if (!w) return
  w.document.write(
    `<!doctype html><html><head><meta charset="utf-8"><title>Comanda</title><style>${TICKET_CSS}</style></head><body>${bodyHtml}</body></html>`
  )
  w.document.close()
  w.focus()
  w.print()
}
