import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { ReservationDTO, ServiceTurn } from "@/api/types-reservations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  useCreateReservation,
  useReservations,
  useReservationTransition,
} from "@/hooks/use-reservations"
import { useTables } from "@/hooks/use-tables"
import { formatReservedTime, RESERVATION_STATUS_VARIANT, toReservedAtIso } from "@/lib/reservations"

const NO_TABLE = "none"

function todayLocal(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// Alta de reserva. Internal so the page file exports only the page component.
function NewReservationSheet({ defaultDate }: { defaultDate: string }) {
  const { t } = useTranslation()
  const create = useCreateReservation()
  const tables = useTables()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [phone, setPhone] = useState("")
  const [partySize, setPartySize] = useState("2")
  const [date, setDate] = useState(defaultDate)
  const [time, setTime] = useState("21:00")
  const [turn, setTurn] = useState<ServiceTurn>("DINNER")
  const [tableId, setTableId] = useState(NO_TABLE)
  const [note, setNote] = useState("")

  const submit = () => {
    if (!name.trim()) {
      toast.error(t("reservations.toasts.customerNameRequired"))
      return
    }
    const size = Number(partySize)
    if (!Number.isInteger(size) || size < 1) {
      toast.error(t("reservations.toasts.partySizeInvalid"))
      return
    }
    if (!date || !time) {
      toast.error(t("reservations.toasts.dateTimeRequired"))
      return
    }
    create.mutate(
      {
        customer_name: name.trim(),
        party_size: size,
        reserved_at: toReservedAtIso(date, time),
        turn,
        customer_phone: phone.trim() || null,
        table_id: tableId === NO_TABLE ? null : tableId,
        note: note.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success(t("reservations.toasts.created"))
          setName("")
          setPhone("")
          setPartySize("2")
          setNote("")
          setTableId(NO_TABLE)
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("reservations.toasts.createError"))),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button>{t("reservations.form.new")}</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("reservations.form.new")}</SheetTitle>
          <SheetDescription>{t("reservations.form.description")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            placeholder={t("reservations.form.customer")}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder={t("reservations.form.phone")}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <div className="flex gap-2">
            <Input
              type="number"
              min={1}
              placeholder={t("reservations.form.guests")}
              value={partySize}
              onChange={(e) => setPartySize(e.target.value)}
              className="max-w-[7rem]"
            />
            <Select value={turn} onValueChange={(v) => setTurn(v as ServiceTurn)}>
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="LUNCH">{t("reservations.turnLabels.LUNCH")}</SelectItem>
                <SelectItem value="DINNER">{t("reservations.turnLabels.DINNER")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
          <Select value={tableId} onValueChange={setTableId}>
            <SelectTrigger>
              <SelectValue placeholder={t("reservations.form.table")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_TABLE}>{t("reservations.form.noTable")}</SelectItem>
              {tables.data?.map((table) => (
                <SelectItem key={table.id} value={table.id}>
                  {t("reservations.tableOption", { number: table.number })}
                  {table.name ? ` · ${table.name}` : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            placeholder={t("reservations.form.note")}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? t("reservations.form.creating") : t("reservations.form.submit")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function RowActions({ reservation }: { reservation: ReservationDTO }) {
  const { t } = useTranslation()
  const transition = useReservationTransition()

  const act = (action: "confirm" | "seat" | "complete" | "cancel" | "noShow") =>
    transition.mutate(
      { id: reservation.id, action },
      {
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("reservations.toasts.transitionError"))),
      }
    )

  const status = reservation.status
  if (status === "COMPLETED" || status === "CANCELLED" || status === "NO_SHOW") {
    return <span className="text-muted-foreground">—</span>
  }

  return (
    <div className="flex flex-wrap justify-end gap-1">
      {status === "PENDING" ? (
        <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("confirm")}>
          {t("reservations.actions.confirm")}
        </Button>
      ) : null}
      {status === "PENDING" || status === "CONFIRMED" ? (
        <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("seat")}>
          {t("reservations.actions.seat")}
        </Button>
      ) : null}
      {status === "SEATED" ? (
        <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("complete")}>
          {t("reservations.actions.complete")}
        </Button>
      ) : null}
      {status === "PENDING" || status === "CONFIRMED" ? (
        <>
          <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("noShow")}>
            {t("reservations.actions.noShow")}
          </Button>
          <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("cancel")}>
            {t("reservations.actions.cancel")}
          </Button>
        </>
      ) : null}
    </div>
  )
}

export function ReservationsPage() {
  const { t } = useTranslation()
  const [date, setDate] = useState(() => todayLocal())
  const [turnFilter, setTurnFilter] = useState<"ALL" | ServiceTurn>("ALL")

  const from = date ? new Date(`${date}T00:00:00`).toISOString() : undefined
  const to = date ? new Date(`${date}T23:59:59`).toISOString() : undefined

  const reservations = useReservations({
    from,
    to,
    turn: turnFilter === "ALL" ? undefined : turnFilter,
  })

  const tables = useTables()
  const tableLabel = (tableId: string | null) => {
    if (!tableId) return "—"
    const table = tables.data?.find((item) => item.id === tableId)
    return table ? t("reservations.tableOption", { number: table.number }) : "—"
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("reservations.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            {t("reservations.subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("reservations.dayLabel")}
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("reservations.shiftLabel")}
            <Select value={turnFilter} onValueChange={(v) => setTurnFilter(v as "ALL" | ServiceTurn)}>
              <SelectTrigger className="w-[8rem]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t("reservations.filterAll")}</SelectItem>
                <SelectItem value="LUNCH">{t("reservations.turnLabels.LUNCH")}</SelectItem>
                <SelectItem value="DINNER">{t("reservations.turnLabels.DINNER")}</SelectItem>
              </SelectContent>
            </Select>
          </label>
          <NewReservationSheet defaultDate={date} />
        </div>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {reservations.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : reservations.data && reservations.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("reservations.columns.time")}</TableHead>
                <TableHead>{t("reservations.columns.customer")}</TableHead>
                <TableHead className="text-right">{t("reservations.columns.guests")}</TableHead>
                <TableHead>{t("reservations.columns.shift")}</TableHead>
                <TableHead>{t("reservations.columns.table")}</TableHead>
                <TableHead>{t("reservations.columns.status")}</TableHead>
                <TableHead className="text-right">{t("reservations.columns.actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reservations.data.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="tabular-nums">{formatReservedTime(r.reserved_at)}</TableCell>
                  <TableCell className="font-medium">
                    {r.customer_name}
                    {r.customer_phone ? (
                      <span className="block text-xs font-normal text-muted-foreground">
                        {r.customer_phone}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{r.party_size}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {t(`reservations.turnLabels.${r.turn}`)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{tableLabel(r.table_id)}</TableCell>
                  <TableCell>
                    <Badge variant={RESERVATION_STATUS_VARIANT[r.status]}>
                      {t(`reservations.statusLabels.${r.status}`)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <RowActions reservation={r} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState>
            {t("reservations.emptyState")}
          </EmptyState>
        )}
      </div>
    </div>
  )
}
