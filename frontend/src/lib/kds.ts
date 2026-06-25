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
