import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { Zap } from "lucide-react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { FloorTableDTO, SectorDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useFloor } from "@/hooks/use-floor"
import { useCreateOrder } from "@/hooks/use-orders"
import { useRealtimeEvent } from "@/hooks/use-realtime"
import { useSectors } from "@/hooks/use-sectors"
import { useRequestBill } from "@/hooks/use-sessions"
import { useCreateTable } from "@/hooks/use-tables"
import { filterFloor, type FloorChip } from "@/lib/floor-filter"
import { floorView, type FloorView } from "@/lib/floor-session"
import { kdsDelay } from "@/lib/kds"
import { formatMoney } from "@/lib/money"

const CHIPS: { key: FloorChip; labelKey: string }[] = [
  { key: "all", labelKey: "floor.chips.all" },
  { key: "to_serve", labelKey: "floor.chips.toServe" },
  { key: "to_charge", labelKey: "floor.chips.toCharge" },
  { key: "mine", labelKey: "floor.chips.mine" },
  { key: "free", labelKey: "floor.chips.free" },
]

const SIN_SECTOR = "__none__"

// Card tone by derived state — attention states pop, "libre" stays neutral (no
// green, per the spec).
function cardClass(view: FloorView): string {
  const base = "cursor-pointer transition-colors"
  switch (view.state) {
    case "FREE":
      return base + "hover:bg-muted/50"
    case "TO_SERVE":
      return base + "border-warning/70 bg-warning/10"
    case "TO_CHARGE":
      return base + "border-primary/70 bg-primary/10"
    case "SERVED":
      return base + "border-success/60 bg-success/10"
    default:
      return base + "border-primary/40 bg-muted/40"
  }
}

function TableCard({
  table,
  now,
  onOpen,
  onBill,
  billPending,
}: {
  table: FloorTableDTO
  now: number
  onOpen: (t: FloorTableDTO) => void
  onBill: (sessionId: string) => void
  billPending: boolean
}) {
  const { t } = useTranslation()
  const view = floorView(table)
  const order = table.active_order
  const delay = view.since ? kdsDelay(view.since, now) : null
  const canBill = table.session != null && view.state !== "TO_CHARGE" && view.state !== "FREE"
  return (
    <Card onClick={() => onOpen(table)} className={cardClass(view)}>
      <CardContent className="flex flex-col items-center justify-center gap-1 py-5">
        <div className="flex items-center gap-1.5">
          <span className="font-heading text-2xl font-medium">{table.number}</span>
          {view.pax ? (
            <span className="text-xs text-muted-foreground">
              {t("floor.pax", { count: view.pax })}
            </span>
          ) : null}
        </div>
        {table.name ? (
          <span className="text-xs text-muted-foreground">{table.name}</span>
        ) : null}
        {view.state !== "FREE" ? (
          <>
            <Badge variant={view.attention ? "default" : "secondary"} className="mt-1 gap-1">
              {view.state === "TO_SERVE" ? <Zap className="size-3" /> : null}
              {t(`floor.state.${view.state}`)}
            </Badge>
            {order ? (
              <span className="text-xs font-medium">
                {formatMoney(order.total_amount, order.currency)}
              </span>
            ) : null}
            {view.waiterName ? (
              <span className="text-[11px] text-muted-foreground">{view.waiterName}</span>
            ) : null}
            {delay ? (
              <span
                className={
                  "text-[11px] " +
                  (view.attention && delay.level === "late"
                    ? "font-medium text-destructive"
                    : view.attention && delay.level === "warn"
                      ? "font-medium text-warning"
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
                disabled={billPending}
                onClick={(e) => {
                  e.stopPropagation()
                  onBill(table.session!.id)
                }}
              >
                {t("floor.requestBill")}
              </Button>
            ) : null}
          </>
        ) : (
          <span className="text-xs text-muted-foreground">{t("floor.state.FREE")}</span>
        )}
      </CardContent>
    </Card>
  )
}

export function FloorPage() {
  const { t } = useTranslation()
  const floor = useFloor()
  const sectors = useSectors()
  const createOrder = useCreateOrder()
  const createTable = useCreateTable()
  const requestBill = useRequestBill()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const { session } = useAuth()
  const canManage = session?.role === "OWNER" || session?.role === "MANAGER"

  // Aviso del comensal desde la carta QR ("llamar al mozo" / "pedir la cuenta").
  // Es una notificación (no refetch): mostramos un toast que perdura.
  useRealtimeEvent("floor", "floor.call", (payload) => {
    const number = payload.table_number ?? "?"
    const key = payload.kind === "bill" ? "floor.toast.bill" : "floor.toast.callWaiter"
    toast(t(key, { number }), { duration: 8000 })
  })
  const [newNumber, setNewNumber] = useState("")
  const [search, setSearch] = useState("")
  const [chip, setChip] = useState<FloorChip>(() =>
    searchParams.get("cobrar") === "1" ? "to_charge" : "all"
  )
  const [now, setNow] = useState(() => Date.now())
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set())

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
        toast.error(apiErrorText(error, t, t("floor.errors.openOrder"))),
    })
  }

  const askForBill = (sessionId: string) => {
    requestBill.mutate(sessionId, {
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("floor.errors.requestBill"))),
    })
  }

  const addTable = () => {
    const n = Number(newNumber)
    if (!Number.isInteger(n) || n <= 0) {
      toast.error(t("floor.errors.invalidNumber"))
      return
    }
    createTable.mutate(
      { number: n, name: null },
      {
        onSuccess: () => {
          toast.success(t("floor.toast.added"))
          setNewNumber("")
          void queryClient.invalidateQueries({ queryKey: ["floor"] })
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("floor.errors.addTable"))),
      }
    )
  }

  const toggleSector = (id: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const tables = floor.data ?? []
  const visible = filterFloor(tables, search, chip, session?.userId)
  const sectorList = sectors.data ?? []
  const hasSectors = sectorList.length > 0
  // Attention strip (§5.4): tables that need a human now, across every sector.
  const attention = hasSectors ? visible.filter((t) => floorView(t).attention) : []

  const card = (t: FloorTableDTO) => (
    <TableCard
      key={t.id}
      table={t}
      now={now}
      onOpen={openTable}
      onBill={askForBill}
      billPending={requestBill.isPending}
    />
  )

  // Group tables by sector (ordered), with a trailing "Sin sector" bucket.
  const groups: { sector: SectorDTO | null; tables: FloorTableDTO[] }[] = []
  if (hasSectors) {
    for (const s of sectorList) {
      const inSector = visible.filter((t) => t.sector_id === s.id)
      if (inSector.length > 0) groups.push({ sector: s, tables: inSector })
    }
    const knownIds = new Set(sectorList.map((s) => s.id))
    const orphans = visible.filter((t) => !t.sector_id || !knownIds.has(t.sector_id))
    if (orphans.length > 0) groups.push({ sector: null, tables: orphans })
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {t("floor.title")}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">{t("floor.subtitle")}</p>
      </header>

      {canManage ? (
        <div className="flex items-end gap-2">
          <Input
            type="number"
            inputMode="numeric"
            placeholder={t("floor.numberPlaceholder")}
            value={newNumber}
            onChange={(e) => setNewNumber(e.target.value)}
            className="max-w-[8rem]"
          />
          <Button variant="outline" onClick={addTable} disabled={createTable.isPending}>
            {t("floor.addTable")}
          </Button>
        </div>
      ) : null}

      {tables.length > 0 ? (
        <div className="flex flex-col gap-2">
          <Input
            placeholder={t("floor.searchPlaceholder")}
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
                {t(c.labelKey)}
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      {attention.length > 0 ? (
        <section className="flex flex-col gap-2 rounded-xl border border-warning/40 bg-warning/10 p-3">
          <p className="text-xs font-semibold text-warning">
            {t("floor.attention", { count: attention.length })}
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{attention.map(card)}</div>
        </section>
      ) : null}

      {floor.isPending ? (
        <Spinner />
      ) : tables.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {canManage ? t("floor.emptyManage") : t("floor.empty")}
        </p>
      ) : visible.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("floor.noMatch")}</p>
      ) : hasSectors ? (
        <div className="flex flex-col gap-4">
          {groups.map(({ sector, tables: group }) => {
            const id = sector?.id ?? SIN_SECTOR
            const isCollapsed = collapsed.has(id)
            return (
              <section key={id} className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => toggleSector(id)}
                  className="flex items-center gap-2 text-left"
                >
                  {sector?.color ? (
                    <span
                      className="size-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: sector.color }}
                    />
                  ) : null}
                  <span className="text-sm font-semibold text-foreground">
                    {sector?.name ?? t("floor.sinSector")}
                  </span>
                  <span className="text-xs text-muted-foreground">({group.length})</span>
                  <span className="text-xs text-muted-foreground">
                    {isCollapsed ? "▸" : "▾"}
                  </span>
                </button>
                {isCollapsed ? null : (
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {group.map(card)}
                  </div>
                )}
              </section>
            )
          })}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{visible.map(card)}</div>
      )}
    </div>
  )
}
