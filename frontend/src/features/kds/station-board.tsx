import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { ItemAction } from "@/api/orders-api"
import type { Station } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useKdsOrders } from "@/hooks/use-kds-orders"
import { useAdvanceItem } from "@/hooks/use-orders"
import { useTables } from "@/hooks/use-tables"
import type { KdsDelayLevel } from "@/lib/kds"
import { kdsDelay, kdsTickets, playNewOrderChime } from "@/lib/kds"

const DELAY_BORDER: Record<KdsDelayLevel, string> = {
  fresh: "border-border",
  warn: "border-amber-400",
  late: "border-red-500",
}

// One station's live board (Cocina or Barra). Renders per-item tickets, oldest
// first, and bumps them one by one — the backbone that lets a coffee go to the
// bar while the food goes to the kitchen.
export function StationBoard({
  station,
  title,
  subtitle,
}: {
  station: Station
  title: string
  subtitle: string
}) {
  const kds = useKdsOrders(station)
  const tables = useTables()
  const advance = useAdvanceItem()
  const [now, setNow] = useState(() => Date.now())
  const seen = useRef<Set<string>>(new Set())

  // Tick so the waiting timers stay current even with no new events.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  const tickets = kds.data ? kdsTickets(kds.data, station) : []

  // Chime when an item appears that we hadn't seen (skips the first load).
  useEffect(() => {
    if (!kds.data) return
    const ids = new Set(tickets.map((t) => t.item.id))
    if (seen.current.size > 0 && [...ids].some((id) => !seen.current.has(id))) {
      playNewOrderChime()
    }
    seen.current = ids
    // tickets is derived from kds.data; depending on kds.data is enough.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kds.data])

  const tableNumber = (tableId: string): string => {
    const found = tables.data?.find((t) => t.id === tableId)
    return found ? String(found.number) : "—"
  }

  const bump = (orderId: string, itemId: string, action: ItemAction) => {
    advance.mutate(
      { orderId, itemId, action },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No se pudo actualizar el ítem."),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {title}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </header>

      {kds.isPending ? (
        <Spinner />
      ) : tickets.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tickets.map((t) => {
            const delay = kdsDelay(t.item.sent_at, now)
            return (
              <Card key={t.item.id} className={DELAY_BORDER[delay.level]}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Mesa {tableNumber(t.tableId)}</span>
                    <span className="flex items-center gap-2 text-xs font-normal text-muted-foreground">
                      {delay.level === "late" ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 font-medium text-red-700">
                          demora
                        </span>
                      ) : null}
                      <span className="tabular-nums">{delay.minutes}′</span>
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <p className="text-sm">
                    <span className="font-medium">
                      {t.item.quantity}× {t.item.name}
                    </span>
                    {t.item.note ? (
                      <span className="text-muted-foreground"> ({t.item.note})</span>
                    ) : null}
                  </p>
                  {t.item.status === "SENT" ? (
                    <Button
                      variant="outline"
                      className="h-11 w-full"
                      onClick={() => bump(t.orderId, t.item.id, "preparing")}
                    >
                      Empezar a preparar
                    </Button>
                  ) : (
                    <Button
                      className="h-11 w-full"
                      onClick={() => bump(t.orderId, t.item.id, "ready")}
                    >
                      Marcar listo
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No hay ítems en {title.toLowerCase()}.</p>
      )}
    </div>
  )
}
