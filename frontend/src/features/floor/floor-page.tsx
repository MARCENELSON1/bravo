import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { FloorTableDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useFloor } from "@/hooks/use-floor"
import { useCreateOrder } from "@/hooks/use-orders"
import { useRequestBill } from "@/hooks/use-sessions"
import { useCreateTable } from "@/hooks/use-tables"
import { filterFloor, type FloorChip } from "@/lib/floor-filter"
import { floorView, type FloorView } from "@/lib/floor-session"
import { kdsDelay } from "@/lib/kds"
import { formatMoney } from "@/lib/money"

const CHIPS: { key: FloorChip; label: string }[] = [
  { key: "all", label: "Todas" },
  { key: "to_serve", label: "Para servir" },
  { key: "to_charge", label: "A cobrar" },
  { key: "mine", label: "Mis mesas" },
  { key: "free", label: "Libres" },
]

// Card tone by derived state — attention states pop, "libre" stays neutral (no
// green, per the spec).
function cardClass(view: FloorView): string {
  const base = "cursor-pointer transition-colors "
  switch (view.state) {
    case "FREE":
      return base + "hover:bg-muted/50"
    case "TO_SERVE":
      return base + "border-amber-500/70 bg-amber-50/50 dark:bg-amber-500/10"
    case "TO_CHARGE":
      return base + "border-primary/70 bg-primary/10"
    case "SERVED":
      return base + "border-emerald-500/60 bg-emerald-50/40 dark:bg-emerald-500/10"
    default:
      return base + "border-primary/40 bg-muted/40"
  }
}

export function FloorPage() {
  const floor = useFloor()
  const createOrder = useCreateOrder()
  const createTable = useCreateTable()
  const requestBill = useRequestBill()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const { session } = useAuth()
  const canManage = session?.role === "OWNER" || session?.role === "MANAGER"
  const [newNumber, setNewNumber] = useState("")
  const [search, setSearch] = useState("")
  const [chip, setChip] = useState<FloorChip>(() =>
    searchParams.get("cobrar") === "1" ? "to_charge" : "all"
  )
  const [now, setNow] = useState(() => Date.now())

  // Tick so the per-table waiting timers stay current between refetches.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  const openTable = (table: FloorTableDTO) => {
    // Occupied → open the existing order (never create a duplicate).
    if (table.active_order) {
      navigate(`/app/orders/${table.active_order.id}`)
      return
    }
    createOrder.mutate(table.id, {
      onSuccess: (res) => navigate(`/app/orders/${res.order_id}`),
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos abrir la comanda."),
    })
  }

  const askForBill = (sessionId: string) => {
    requestBill.mutate(sessionId, {
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos pedir la cuenta."),
    })
  }

  const addTable = () => {
    const n = Number(newNumber)
    if (!Number.isInteger(n) || n <= 0) {
      toast.error("Número de mesa inválido.")
      return
    }
    createTable.mutate(
      { number: n, name: null },
      {
        onSuccess: () => {
          toast.success("Mesa agregada.")
          setNewNumber("")
          void queryClient.invalidateQueries({ queryKey: ["floor"] })
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos agregar la mesa."),
      }
    )
  }

  const tables = floor.data ?? []
  const visible = filterFloor(tables, search, chip, session?.userId)

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Mesas
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          En vivo: para servir / a cobrar / en cocina. Tocá una mesa para abrir su comanda.
        </p>
      </header>

      {canManage ? (
        <div className="flex items-end gap-2">
          <Input
            type="number"
            inputMode="numeric"
            placeholder="N° de mesa"
            value={newNumber}
            onChange={(e) => setNewNumber(e.target.value)}
            className="max-w-[8rem]"
          />
          <Button variant="outline" onClick={addTable} disabled={createTable.isPending}>
            Agregar mesa
          </Button>
        </div>
      ) : null}

      {tables.length > 0 ? (
        <div className="flex flex-col gap-2">
          <Input
            placeholder="Buscar mesa…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-[12rem]"
          />
          <div className="flex flex-wrap gap-2">
            {CHIPS.map((c) => (
              <Button
                key={c.key}
                size="sm"
                variant={chip === c.key ? "default" : "outline"}
                onClick={() => setChip(c.key)}
              >
                {c.label}
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      {floor.isPending ? (
        <Spinner />
      ) : tables.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No hay mesas todavía{canManage ? " — agregá una arriba." : "."}
        </p>
      ) : visible.length === 0 ? (
        <p className="text-sm text-muted-foreground">No hay mesas que coincidan.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {visible.map((t) => {
            const view = floorView(t)
            const order = t.active_order
            const delay = view.since ? kdsDelay(view.since, now) : null
            const canBill =
              t.session != null && view.state !== "TO_CHARGE" && view.state !== "FREE"
            return (
              <Card key={t.id} onClick={() => openTable(t)} className={cardClass(view)}>
                <CardContent className="flex flex-col items-center justify-center gap-1 py-5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-heading text-2xl font-medium">{t.number}</span>
                    {view.pax ? (
                      <span className="text-xs text-muted-foreground">· {view.pax}p</span>
                    ) : null}
                  </div>
                  {t.name ? (
                    <span className="text-xs text-muted-foreground">{t.name}</span>
                  ) : null}
                  {view.state !== "FREE" ? (
                    <>
                      <Badge
                        variant={view.attention ? "default" : "secondary"}
                        className="mt-1"
                      >
                        {view.label}
                      </Badge>
                      {order ? (
                        <span className="text-xs font-medium">
                          {formatMoney(order.total_amount, order.currency)}
                        </span>
                      ) : null}
                      {view.waiterName ? (
                        <span className="text-[11px] text-muted-foreground">
                          {view.waiterName}
                        </span>
                      ) : null}
                      {delay ? (
                        <span
                          className={
                            "text-[11px] " +
                            (view.attention && delay.level === "late"
                              ? "font-medium text-destructive"
                              : view.attention && delay.level === "warn"
                                ? "font-medium text-amber-600 dark:text-amber-400"
                                : "text-muted-foreground")
                          }
                        >
                          {delay.minutes}′
                        </span>
                      ) : null}
                      {canBill ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="mt-1 h-6 px-2 text-[11px]"
                          disabled={requestBill.isPending}
                          onClick={(e) => {
                            e.stopPropagation()
                            askForBill(t.session!.id)
                          }}
                        >
                          Pedir cuenta
                        </Button>
                      ) : null}
                    </>
                  ) : (
                    <span className="text-xs text-muted-foreground">Libre</span>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
