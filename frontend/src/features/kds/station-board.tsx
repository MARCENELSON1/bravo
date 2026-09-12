import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { CourseAction } from "@/api/orders-api"
import type { Course, KdsTicket, Station } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useKdsOrders } from "@/hooks/use-kds-orders"
import { useAdvanceCourse } from "@/hooks/use-orders"
import { useTables } from "@/hooks/use-tables"
import type { KdsDelayLevel } from "@/lib/kds"
import { kdsDelay, kdsTickets, playNewOrderChime } from "@/lib/kds"

const DELAY_BORDER: Record<KdsDelayLevel, string> = {
  fresh: "border-border",
  warn: "border-warning",
  late: "border-destructive",
}

// Identidad de un ticket = comanda + curso (lo que se bumpea de una).
const ticketKey = (ticket: KdsTicket): string => `${ticket.orderId}:${ticket.course}`

// One station's live board (Cocina or Barra). Un ticket por (mesa, CURSO) con
// todos sus platos: la cocina lo bumpea entero — "Empezar" cuando lo pone al
// fuego y "Listo" cuando terminó el tiempo completo. Un curso en espera se ve
// (para el mise en place) pero no se cocina hasta que el mozo lo marche.
export function StationBoard({
  station,
  title,
  subtitle,
}: {
  station: Station
  title: string
  subtitle: string
}) {
  const { t } = useTranslation()
  const kds = useKdsOrders(station)
  const tables = useTables()
  const advance = useAdvanceCourse()
  const [now, setNow] = useState(() => Date.now())
  const seen = useRef<Set<string>>(new Set())

  // Tick so the waiting timers stay current even with no new events.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  const tickets = kds.data ? kdsTickets(kds.data, station) : []

  // Chime when a ticket appears that we hadn't seen (skips the first load).
  useEffect(() => {
    if (!kds.data) return
    const ids = new Set(tickets.map(ticketKey))
    if (seen.current.size > 0 && [...ids].some((id) => !seen.current.has(id))) {
      playNewOrderChime()
    }
    seen.current = ids
    // tickets is derived from kds.data; depending on kds.data is enough.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kds.data])

  const tableNumber = (tableId: string): string => {
    const found = tables.data?.find((table) => table.id === tableId)
    return found ? String(found.number) : "—"
  }

  const courseLabel = (course: Course): string => t(`kds.courses.${course}`)

  const bump = (orderId: string, course: Course, action: CourseAction) => {
    advance.mutate(
      { orderId, course, action, station },
      {
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("kds.errors.courseUpdateFailed"))),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
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
          {tickets.map((ticket) => {
            const delay = kdsDelay(ticket.sentAt, now)
            return (
              <Card
                key={ticketKey(ticket)}
                // En espera: se ve, no apura (sin borde de demora ni timer).
                className={ticket.held ? "border-border opacity-60" : DELAY_BORDER[delay.level]}
              >
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-2">
                    <span>
                      {t("kds.tableLabel", { number: tableNumber(ticket.tableId) })} ·{" "}
                      {courseLabel(ticket.course)}
                    </span>
                    {ticket.held ? (
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        {t("kds.onHold")}
                      </span>
                    ) : (
                      <span className="flex items-center gap-2 text-xs font-normal text-muted-foreground">
                        {delay.level === "late" ? (
                          <span className="rounded-full bg-destructive/10 px-2 py-0.5 font-medium text-destructive">
                            {t("kds.delayed")}
                          </span>
                        ) : null}
                        <span className="tabular-nums">{delay.minutes}′</span>
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <ul className="flex flex-col gap-1 text-sm">
                    {ticket.items.map((item) => (
                      <li key={item.id}>
                        <span className="font-medium">
                          {item.quantity}× {item.name}
                        </span>
                        {item.selected_options && item.selected_options.length > 0 ? (
                          <span className="block text-xs text-muted-foreground">
                            {item.selected_options.map((option) => option.name).join(" · ")}
                          </span>
                        ) : null}
                        {item.note ? (
                          <span className="block text-xs text-muted-foreground">
                            › {item.note}
                          </span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                  {/* El curso entero de una: el mozo pidió "listo cuando termines
                      todo el tiempo", no plato por plato. */}
                  {ticket.held ? null : ticket.canStart ? (
                    <Button
                      variant="outline"
                      className="h-11 w-full"
                      onClick={() => bump(ticket.orderId, ticket.course, "preparing")}
                    >
                      {t("kds.startPreparing")}
                    </Button>
                  ) : (
                    <Button
                      className="h-11 w-full"
                      onClick={() => bump(ticket.orderId, ticket.course, "ready")}
                    >
                      {t("kds.markReady")}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          {t("kds.empty", { station: title.toLowerCase() })}
        </p>
      )}
    </div>
  )
}
