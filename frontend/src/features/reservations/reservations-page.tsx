import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { ReservationDTO, ServiceTurn } from "@/api/types-reservations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
import {
  formatReservedTime,
  RESERVATION_STATUS_LABELS,
  RESERVATION_STATUS_VARIANT,
  SERVICE_TURN_LABELS,
  toReservedAtIso,
} from "@/lib/reservations"

const NO_TABLE = "none"

function todayLocal(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// Alta de reserva. Internal so the page file exports only the page component.
function NewReservationSheet({ defaultDate }: { defaultDate: string }) {
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
      toast.error("Ingresá el nombre del cliente.")
      return
    }
    const size = Number(partySize)
    if (!Number.isInteger(size) || size < 1) {
      toast.error("Ingresá una cantidad de personas válida.")
      return
    }
    if (!date || !time) {
      toast.error("Ingresá fecha y hora.")
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
          toast.success("Reserva creada.")
          setName("")
          setPhone("")
          setPartySize("2")
          setNote("")
          setTableId(NO_TABLE)
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos crear la reserva."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button>Nueva reserva</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Nueva reserva</SheetTitle>
          <SheetDescription>Cliente, personas, fecha/hora y turno. Mesa opcional.</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input placeholder="Cliente" value={name} onChange={(e) => setName(e.target.value)} />
          <Input
            placeholder="Teléfono (opcional)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <div className="flex gap-2">
            <Input
              type="number"
              min={1}
              placeholder="Personas"
              value={partySize}
              onChange={(e) => setPartySize(e.target.value)}
              className="max-w-[7rem]"
            />
            <Select value={turn} onValueChange={(v) => setTurn(v as ServiceTurn)}>
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="LUNCH">Almuerzo</SelectItem>
                <SelectItem value="DINNER">Cena</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
          <Select value={tableId} onValueChange={setTableId}>
            <SelectTrigger>
              <SelectValue placeholder="Mesa (opcional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_TABLE}>Sin mesa</SelectItem>
              {tables.data?.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  Mesa {t.number}
                  {t.name ? ` · ${t.name}` : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            placeholder="Nota (opcional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? "Creando…" : "Crear reserva"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function RowActions({ reservation }: { reservation: ReservationDTO }) {
  const transition = useReservationTransition()

  const act = (action: "confirm" | "seat" | "complete" | "cancel" | "noShow") =>
    transition.mutate(
      { id: reservation.id, action },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos actualizar la reserva."),
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
          Confirmar
        </Button>
      ) : null}
      {status === "PENDING" || status === "CONFIRMED" ? (
        <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("seat")}>
          Sentar
        </Button>
      ) : null}
      {status === "SEATED" ? (
        <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("complete")}>
          Completar
        </Button>
      ) : null}
      {status === "PENDING" || status === "CONFIRMED" ? (
        <>
          <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("noShow")}>
            No-show
          </Button>
          <Button variant="ghost" size="sm" disabled={transition.isPending} onClick={() => act("cancel")}>
            Cancelar
          </Button>
        </>
      ) : null}
    </div>
  )
}

export function ReservationsPage() {
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
    const table = tables.data?.find((t) => t.id === tableId)
    return table ? `Mesa ${table.number}` : "—"
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Reservas
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            Agenda del servicio por día y turno. Confirmá, sentá y registrá no-shows.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Día
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Turno
            <Select value={turnFilter} onValueChange={(v) => setTurnFilter(v as "ALL" | ServiceTurn)}>
              <SelectTrigger className="w-[8rem]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todos</SelectItem>
                <SelectItem value="LUNCH">Almuerzo</SelectItem>
                <SelectItem value="DINNER">Cena</SelectItem>
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
                <TableHead>Hora</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead className="text-right">Personas</TableHead>
                <TableHead>Turno</TableHead>
                <TableHead>Mesa</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
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
                    {SERVICE_TURN_LABELS[r.turn]}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{tableLabel(r.table_id)}</TableCell>
                  <TableCell>
                    <Badge variant={RESERVATION_STATUS_VARIANT[r.status]}>
                      {RESERVATION_STATUS_LABELS[r.status]}
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
          <p className="p-8 text-center text-sm text-muted-foreground">
            No hay reservas para este día.
          </p>
        )}
      </div>
    </div>
  )
}
