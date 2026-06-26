import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { OrderAction } from "@/api/orders-api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useKdsOrders } from "@/hooks/use-kds-orders"
import { useAdvanceOrder } from "@/hooks/use-orders"
import { useTables } from "@/hooks/use-tables"
import type { KdsDelayLevel } from "@/lib/kds"
import { kdsDelay } from "@/lib/kds"

const DELAY_BORDER: Record<KdsDelayLevel, string> = {
  fresh: "border-border",
  warn: "border-amber-400",
  late: "border-red-500",
}

// A short chime when a new ticket lands. Best-effort: if audio is blocked the
// visual cue (the new card) is enough.
function playNewOrderChime(): void {
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

export function KdsPage() {
  const kds = useKdsOrders()
  const tables = useTables()
  const advance = useAdvanceOrder()
  const [now, setNow] = useState(() => Date.now())
  const seen = useRef<Set<string>>(new Set())

  // Tick so the waiting timers stay current even with no new events.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  // Chime when a ticket appears that we hadn't seen (skips the first load).
  useEffect(() => {
    if (!kds.data) return
    const ids = new Set(kds.data.map((o) => o.id))
    if (seen.current.size > 0 && kds.data.some((o) => !seen.current.has(o.id))) {
      playNewOrderChime()
    }
    seen.current = ids
  }, [kds.data])

  const tableNumber = (tableId: string): string => {
    const found = tables.data?.find((t) => t.id === tableId)
    return found ? String(found.number) : "—"
  }

  const advanceTo = (orderId: string, action: OrderAction) => {
    advance.mutate(
      { orderId, action },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No se pudo actualizar la comanda."),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Cocina (KDS)
        </GradientHeading>
        <p className="text-sm text-muted-foreground">Comandas en preparación, en vivo.</p>
      </header>

      {kds.isPending ? (
        <Spinner />
      ) : kds.data && kds.data.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {kds.data.map((o) => {
            const delay = kdsDelay(o.created_at, now)
            return (
              <Card key={o.id} className={DELAY_BORDER[delay.level]}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Mesa {tableNumber(o.table_id)}</span>
                    <span className="flex items-center gap-2 text-xs font-normal text-muted-foreground">
                      <span className="tabular-nums">{delay.minutes}′</span>
                      <span>{o.status}</span>
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <ul className="flex flex-col gap-1 text-sm">
                    {o.items.map((it) => (
                      <li key={it.id}>
                        {it.quantity}× {it.name}
                        {it.note ? (
                          <span className="text-muted-foreground"> ({it.note})</span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                  {o.status === "SENT" ? (
                    <Button
                      variant="outline"
                      className="h-11 w-full"
                      onClick={() => advanceTo(o.id, "preparing")}
                    >
                      Empezar a preparar
                    </Button>
                  ) : (
                    <Button className="h-11 w-full" onClick={() => advanceTo(o.id, "ready")}>
                      Marcar listo
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No hay comandas en cocina.</p>
      )}
    </div>
  )
}
