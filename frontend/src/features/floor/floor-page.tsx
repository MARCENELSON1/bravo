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
import { useCreateTable } from "@/hooks/use-tables"
import { filterFloor } from "@/lib/floor-filter"
import { kdsDelay } from "@/lib/kds"
import { formatMoney } from "@/lib/money"

const ORDER_STATUS_LABELS: Record<string, string> = {
  OPEN: "Abierta",
  SENT: "En cocina",
  PREPARING: "Preparando",
  READY: "Lista",
  SERVED: "Servida",
}

function cardClass(order: FloorTableDTO["active_order"]): string {
  const base = "cursor-pointer transition-colors "
  if (!order) return base + "hover:bg-muted/50"
  if (order.status === "SERVED") return base + "border-emerald-500/60 bg-emerald-50/40"
  return base + "border-primary/50 bg-muted/40"
}

export function FloorPage() {
  const floor = useFloor()
  const createOrder = useCreateOrder()
  const createTable = useCreateTable()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const { session } = useAuth()
  const canManage = session?.role === "OWNER" || session?.role === "MANAGER"
  const [newNumber, setNewNumber] = useState("")
  const [search, setSearch] = useState("")
  const [onlyToCharge, setOnlyToCharge] = useState(() => searchParams.get("cobrar") === "1")
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
  const visible = filterFloor(tables, search, onlyToCharge)

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Mesas
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          En vivo: libre / ocupada / a cobrar. Tocá una mesa para abrir su comanda.
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
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Buscar mesa…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-[12rem]"
          />
          <Button
            variant={onlyToCharge ? "default" : "outline"}
            onClick={() => setOnlyToCharge((v) => !v)}
          >
            Solo a cobrar
          </Button>
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
            const order = t.active_order
            const delay = order ? kdsDelay(order.created_at, now) : null
            const serving = order?.status === "SERVED"
            return (
              <Card key={t.id} onClick={() => openTable(t)} className={cardClass(order)}>
                <CardContent className="flex flex-col items-center justify-center gap-1 py-5">
                  <span className="font-heading text-2xl font-medium">{t.number}</span>
                  {t.name ? (
                    <span className="text-xs text-muted-foreground">{t.name}</span>
                  ) : null}
                  {order ? (
                    <>
                      <Badge variant="secondary" className="mt-1">
                        {serving ? "A cobrar" : (ORDER_STATUS_LABELS[order.status] ?? order.status)}
                      </Badge>
                      <span className="text-xs font-medium">
                        {formatMoney(order.total_amount, order.currency)}
                      </span>
                      {delay ? (
                        <span className="text-[11px] text-muted-foreground">{delay.minutes}′</span>
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
