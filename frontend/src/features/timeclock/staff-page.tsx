import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { ShiftDTO } from "@/api/types-timeclock"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
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
import { useAdjustShift, useShifts, useStaffReport } from "@/hooks/use-timeclock"
import { formatMoney } from "@/lib/money"
import {
  formatDateTime,
  formatMinutes,
  fromDateTimeLocal,
  SHIFT_SOURCE_LABELS,
  toDateTimeLocal,
} from "@/lib/timeclock"

// Manager correction for a single shift. Internal (not exported) so the page
// file exports only the page component.
function AdjustSheet({ shift }: { shift: ShiftDTO }) {
  const adjust = useAdjustShift()
  const [open, setOpen] = useState(false)
  const [clockIn, setClockIn] = useState(() => toDateTimeLocal(shift.clock_in_at))
  const [clockOut, setClockOut] = useState(() =>
    shift.clock_out_at ? toDateTimeLocal(shift.clock_out_at) : ""
  )

  const submit = () => {
    if (!clockIn) {
      toast.error("Ingresá la hora de entrada.")
      return
    }
    adjust.mutate(
      {
        shiftId: shift.id,
        body: {
          clock_in_at: fromDateTimeLocal(clockIn),
          clock_out_at: clockOut ? fromDateTimeLocal(clockOut) : null,
        },
      },
      {
        onSuccess: () => {
          toast.success("Fichaje corregido.")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos corregir el fichaje."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          Corregir
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Corregir fichaje</SheetTitle>
          <SheetDescription>Quedará registrado como corrección del encargado.</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <label className="flex flex-col gap-1 text-sm">
            Entrada
            <Input
              type="datetime-local"
              value={clockIn}
              onChange={(e) => setClockIn(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Salida (vacío = turno abierto)
            <Input
              type="datetime-local"
              value={clockOut}
              onChange={(e) => setClockOut(e.target.value)}
            />
          </label>
          <Button onClick={submit} disabled={adjust.isPending}>
            {adjust.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export function StaffPage() {
  const [from, setFrom] = useState("")
  const [to, setTo] = useState("")
  const fromIso = from ? new Date(`${from}T00:00:00`).toISOString() : undefined
  const toIso = to ? new Date(`${to}T23:59:59`).toISOString() : undefined

  const report = useStaffReport({ from: fromIso, to: toIso })
  const shifts = useShifts({ from: fromIso, to: toIso })

  const emailByUser = new Map<string, string>()
  report.data?.rows.forEach((r) => emailByUser.set(r.user_id, r.email))
  const labelFor = (userId: string) => emailByUser.get(userId) ?? userId.slice(0, 8)

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Personal
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            Horas, extras, mesas y ventas por empleado. Corregí fichajes olvidados.
          </p>
        </div>
        <div className="flex items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Desde
            <Input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Hasta
            <Input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="w-auto"
            />
          </label>
        </div>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">Reporte por mozo</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {report.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : report.data && report.data.rows.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Empleado</TableHead>
                  <TableHead className="text-right">Horas</TableHead>
                  <TableHead className="text-right">Extras</TableHead>
                  <TableHead className="text-right">Mesas</TableHead>
                  <TableHead className="text-right">Ventas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.data.rows.map((r) => (
                  <TableRow key={r.user_id}>
                    <TableCell className="font-medium">{r.email || labelFor(r.user_id)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMinutes(r.worked_minutes)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {r.overtime_minutes > 0 ? formatMinutes(r.overtime_minutes) : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{r.tables_served}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(r.sales_amount, r.currency)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-8 text-center text-sm text-muted-foreground">
              No hay datos para el período.
            </p>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">Fichajes</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {shifts.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : shifts.data && shifts.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Empleado</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Salida</TableHead>
                  <TableHead className="text-right">Horas</TableHead>
                  <TableHead>Origen</TableHead>
                  <TableHead className="text-right">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shifts.data.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{labelFor(s.user_id)}</TableCell>
                    <TableCell className="tabular-nums">{formatDateTime(s.clock_in_at)}</TableCell>
                    <TableCell className="tabular-nums">
                      {s.clock_out_at ? formatDateTime(s.clock_out_at) : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {s.worked_minutes !== null ? (
                        formatMinutes(s.worked_minutes)
                      ) : (
                        <Badge variant="secondary">En curso</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{SHIFT_SOURCE_LABELS[s.source] ?? s.source}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <AdjustSheet shift={s} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-8 text-center text-sm text-muted-foreground">
              No hay fichajes para el período.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
