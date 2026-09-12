import type { ItemStatus, KdsTicket, OrderDTO, Station } from "@/api/types-operations"
import { COURSE_ORDER, courseOf } from "@/lib/courses"

// How long an order has been waiting in the kitchen, and a severity level the
// KDS uses to colour the card so cooks see the oldest tickets at a glance.
export type KdsDelayLevel = "fresh" | "warn" | "late"

export function kdsDelay(
  createdAt: string | null,
  nowMs: number
): { minutes: number; level: KdsDelayLevel } {
  if (!createdAt) return { minutes: 0, level: "fresh" }
  const started = Date.parse(createdAt)
  if (Number.isNaN(started)) return { minutes: 0, level: "fresh" }
  const minutes = Math.max(0, Math.floor((nowMs - started) / 60000))
  const level: KdsDelayLevel = minutes >= 10 ? "late" : minutes >= 5 ? "warn" : "fresh"
  return { minutes, level }
}

// Lo que la cocina tiene en mano: al fuego (SENT/PREPARING) y en espera (HELD).
// HELD entra a propósito: la cocina VE el curso que viene para hacer el mise en
// place, aunque todavía no lo cocine.
const _ACTIVE_ITEM_STATUSES = new Set<ItemStatus>(["HELD", "SENT", "PREPARING"])

// Agrupa las comandas de una estación en tickets por (comanda, CURSO): todos
// los platos del tiempo juntos, para que la cocina los bumpee de una sola vez
// ("Listo" cuando terminó el tiempo entero, no plato por plato). Los que están
// al fuego van primero, más viejo arriba; los en espera al final (se ven, no
// apuran).
export function kdsTickets(orders: OrderDTO[], station: Station): KdsTicket[] {
  const tickets: KdsTicket[] = []
  for (const order of orders) {
    const active = order.items.filter(
      (item) => item.station === station && _ACTIVE_ITEM_STATUSES.has(item.status)
    )
    for (const course of COURSE_ORDER) {
      const items = active.filter((item) => courseOf(item) === course)
      if (items.length === 0) continue
      const sentAts = items
        .map((item) => item.sent_at)
        .filter((at): at is string => Boolean(at))
        .sort()
      tickets.push({
        orderId: order.id,
        tableId: order.table_id,
        course,
        items,
        held: items.every((item) => item.status === "HELD"),
        canStart: items.some((item) => item.status === "SENT"),
        sentAt: sentAts[0] ?? null,
      })
    }
  }
  return tickets.sort((a, b) => {
    if (a.held !== b.held) return a.held ? 1 : -1 // en espera al final
    const ta = a.sentAt ? Date.parse(a.sentAt) : 0
    const tb = b.sentAt ? Date.parse(b.sentAt) : 0
    return ta - tb // más viejo primero
  })
}

// A short chime when a new ticket lands. Best-effort: if audio is blocked, the
// visual cue (the new card) is enough.
export function playNewOrderChime(): void {
  try {
    const Ctx =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctx) return
    const ctx = new Ctx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = 880
    gain.gain.setValueAtTime(0.0001, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.01)
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.3)
    osc.start()
    osc.stop(ctx.currentTime + 0.3)
  } catch {
    // No audio available — ignore.
  }
}
