import type { OrderDTO, OrderItemDTO, Station } from "@/api/types-operations"
import { formatMoney } from "@/lib/money"

// Browser-printed comanda ticket (MVP, no hardware): builds a narrow,
// monospace ticket grouped by station so the kitchen and the bar each see their
// own lines. Server-side ESC/POS network printing stays a follow-up behind a
// future TicketPrinter port.

// Etiquetas traducibles del ticket. Se inyectan desde el consumidor (que tiene
// `t()`); los defaults en español dejan las funciones puras y testeables sin
// pasar `t`, y garantizan la paridad AR.
export interface TicketLabels {
  stations: Record<Station, string>
  empty: string
}

const DEFAULT_TICKET_LABELS: TicketLabels = {
  stations: {
    KITCHEN: "COCINA",
    BAR: "BARRA",
  },
  empty: "— sin ítems —",
}

export interface ReceiptLabels {
  nonFiscal: string
  subtotal: string
  tax: (rate: string) => string
  total: string
  tip: string
}

const DEFAULT_RECEIPT_LABELS: ReceiptLabels = {
  nonFiscal: "RECIBO NO FISCAL",
  subtotal: "Subtotal",
  tax: (rate) => `Impuesto (${rate}%)`,
  total: "TOTAL",
  tip: "Propina",
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
  station?: Station,
  labels: TicketLabels = DEFAULT_TICKET_LABELS
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
      return `<div class="station">${labels.stations[st]}</div>${rows}`
    })
    .join("")

  return `<div class="ticket"><div class="head">${escapeHtml(tableLabel)}</div><div class="meta">${escapeHtml(printedAt)}</div>${sections || `<div class="line">${labels.empty}</div>`}</div>`
}

export interface ReceiptPaymentLine {
  label: string
  amount: number // minor units
}

// Desglose de sales tax (US). Todo en minor units. rateBps en puntos básicos.
export interface ReceiptTax {
  subtotal: number
  amount: number
  total: number
  rateBps: number
}

// Pure: a non-fiscal receipt (recibo) for the customer — items + total + how it
// was paid. Not an AFIP comprobante; that's the invoice flow. When `tax` carries
// a positive amount (US), the total is broken out Subtotal/Impuesto/Total; with
// no tax (AR/IVA included) it prints a single TOTAL as before (parity).
export function receiptHtml(
  order: OrderDTO,
  tableLabel: string,
  printedAt: string,
  payments: ReceiptPaymentLine[],
  tipAmount = 0,
  tax: ReceiptTax | null = null,
  labels: ReceiptLabels = DEFAULT_RECEIPT_LABELS
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
  // La propina va aparte del total de la venta (no es ingreso del local).
  const tip =
    tipAmount > 0
      ? `<div class="line">${labels.tip}<span class="amt">${formatMoney(tipAmount, order.currency)}</span></div>`
      : ""
  const totalBlock =
    tax && tax.amount > 0
      ? `<div class="line">${labels.subtotal}<span class="amt">${formatMoney(tax.subtotal, order.currency)}</span></div>` +
        `<div class="line">${labels.tax((tax.rateBps / 100).toFixed(2))}` +
        `<span class="amt">${formatMoney(tax.amount, order.currency)}</span></div>` +
        `<div class="station">${labels.total}<span class="amt">${formatMoney(tax.total, order.currency)}</span></div>`
      : `<div class="station">${labels.total}<span class="amt">${formatMoney(order.total_amount, order.currency)}</span></div>`
  return (
    `<div class="ticket"><div class="head">${escapeHtml(tableLabel)}</div>` +
    `<div class="meta">${labels.nonFiscal} · ${escapeHtml(printedAt)}</div>` +
    `${lines}` +
    `${totalBlock}` +
    `${tip}` +
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
export function printTicket(bodyHtml: string, title = "Comanda"): void {
  const w = window.open("", "_blank", "width=320,height=640")
  if (!w) return
  w.document.write(
    `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${TICKET_CSS}</style></head><body>${bodyHtml}</body></html>`
  )
  w.document.close()
  w.focus()
  w.print()
}
