import type { KdsTicket, OrderDTO, Station } from "@/api/types-operations"

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

// Items still being made (SENT/PREPARING) on the kitchen lifecycle.
const _ACTIVE_ITEM_STATUSES = new Set(["SENT", "PREPARING"])

// Flatten the orders into per-item tickets for one station, oldest first (by
// sent_at). This is what the per-station board renders: a cook bumps items one
// by one, and the order they were marched in is the order they appear.
export function kdsTickets(orders: OrderDTO[], station: Station): KdsTicket[] {
  const tickets: KdsTicket[] = []
  for (const order of orders) {
    for (const item of order.items) {
      if (item.station === station && _ACTIVE_ITEM_STATUSES.has(item.status)) {
        tickets.push({ orderId: order.id, tableId: order.table_id, item })
      }
    }
  }
  return tickets.sort((a, b) => {
    const ta = a.item.sent_at ? Date.parse(a.item.sent_at) : 0
    const tb = b.item.sent_at ? Date.parse(b.item.sent_at) : 0
    return ta - tb // oldest marched first
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
