import { useState } from "react"
import { QRCodeSVG } from "qrcode.react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
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
import {
  useAdjustShift,
  useRegisterPresenceDevice,
  useSetHourlyRate,
  useShifts,
  useStaffReport,
} from "@/hooks/use-timeclock"
import { formatMoney } from "@/lib/money"
import { buildDisplayUrl } from "@/lib/presence"
import {
  formatClock,
  formatDate,
  formatMinutes,
  fromDateTimeLocal,
  isNextDay,
  toDateTimeLocal,
} from "@/lib/timeclock"

// Manager correction for a single shift. Internal (not exported) so the page
// file exports only the page component.
function AdjustSheet({ shift }: { shift: ShiftDTO }) {
  const { t } = useTranslation()
  const adjust = useAdjustShift()
  const [open, setOpen] = useState(false)
  const [clockIn, setClockIn] = useState(() => toDateTimeLocal(shift.clock_in_at))
  const [clockOut, setClockOut] = useState(() =>
    shift.clock_out_at ? toDateTimeLocal(shift.clock_out_at) : ""
  )

  const submit = () => {
    if (!clockIn) {
      toast.error(t("timeclock.adjust.emptyClockIn"))
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
          toast.success(t("timeclock.adjust.corrected"))
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("timeclock.adjust.correctError"))),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("timeclock.adjust.trigger")}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("timeclock.adjust.title")}</SheetTitle>
          <SheetDescription>{t("timeclock.adjust.description")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <label className="flex flex-col gap-1 text-sm">
            {t("timeclock.adjust.clockIn")}
            <Input
              type="datetime-local"
              value={clockIn}
              onChange={(e) => setClockIn(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            {t("timeclock.adjust.clockOut")}
            <Input
              type="datetime-local"
              value={clockOut}
              onChange={(e) => setClockOut(e.target.value)}
            />
          </label>
          <Button onClick={submit} disabled={adjust.isPending}>
            {adjust.isPending ? t("timeclock.adjust.saving") : t("timeclock.adjust.save")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

// OWNER/MANAGER provisions the local display: generates an enrolment link (and a
// QR of it) to open on the screen that will show the rotating fichaje QR.
function DeviceProvisionCard() {
  const { t } = useTranslation()
  const register = useRegisterPresenceDevice()
  const [url, setUrl] = useState<string | null>(null)

  const generate = () => {
    register.mutate(undefined, {
      onSuccess: (device) => setUrl(buildDisplayUrl(device.device_token)),
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("timeclock.device.createError"))),
    })
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline">{t("timeclock.device.trigger")}</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("timeclock.device.title")}</SheetTitle>
          <SheetDescription>{t("timeclock.device.description")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Button onClick={generate} disabled={register.isPending}>
            {register.isPending
              ? t("timeclock.device.generating")
              : url
                ? t("timeclock.device.generateAnother")
                : t("timeclock.device.generate")}
          </Button>
          {url ? (
            <>
              <Input readOnly value={url} onFocus={(e) => e.target.select()} />
              <div className="flex justify-center rounded-xl border border-border bg-white p-4">
                <QRCodeSVG value={url} marginSize={2} className="h-44 w-44" />
              </div>
              <Button variant="outline" onClick={() => window.open(url, "_blank", "noopener")}>
                {t("timeclock.device.openScreen")}
              </Button>
              <p className="text-xs text-muted-foreground">
                {t("timeclock.device.hint")}
              </p>
            </>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  )
}

export function StaffPage() {
  const { t } = useTranslation()
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
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("timeclock.staff.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            {t("timeclock.staff.subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("timeclock.staff.from")}
            <Input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("timeclock.staff.to")}
            <Input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="w-auto"
            />
          </label>
          <DeviceProvisionCard />
        </div>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">{t("timeclock.staff.reportTitle")}</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {report.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : report.data && report.data.rows.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("timeclock.staff.columns.employee")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.hours")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.overtime")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.tables")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.sales")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.hourlyRate")}</TableHead>
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
                    <TableCell className="text-right">
                      <HourlyRateCell userId={r.user_id} rate={r.hourly_rate_amount} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="bg-black/[0.06] p-8 text-center text-sm font-medium text-muted-foreground dark:bg-white/[0.05]">
              {t("timeclock.staff.noReportData")}
            </p>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">{t("timeclock.staff.shiftsTitle")}</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {shifts.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : shifts.data && shifts.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("timeclock.staff.columns.employee")}</TableHead>
                  <TableHead>{t("timeclock.staff.columns.date")}</TableHead>
                  <TableHead>{t("timeclock.staff.columns.clockIn")}</TableHead>
                  <TableHead>{t("timeclock.staff.columns.clockOut")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.hours")}</TableHead>
                  <TableHead>{t("timeclock.staff.columns.source")}</TableHead>
                  <TableHead className="text-right">{t("timeclock.staff.columns.action")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shifts.data.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{labelFor(s.user_id)}</TableCell>
                    <TableCell className="tabular-nums">{formatDate(s.clock_in_at)}</TableCell>
                    <TableCell className="tabular-nums">{formatClock(s.clock_in_at)}</TableCell>
                    <TableCell className="tabular-nums">
                      {s.clock_out_at ? (
                        <>
                          {formatClock(s.clock_out_at)}
                          {isNextDay(s.clock_in_at, s.clock_out_at) ? (
                            <span className="text-muted-foreground"> +1d</span>
                          ) : null}
                        </>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {s.worked_minutes !== null ? (
                        formatMinutes(s.worked_minutes)
                      ) : (
                        <Badge variant="secondary">{t("timeclock.staff.inProgress")}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {t(`timeclock.shiftSource.${s.source}`, { defaultValue: s.source })}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <AdjustSheet shift={s} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="bg-black/[0.06] p-8 text-center text-sm font-medium text-muted-foreground dark:bg-white/[0.05]">
              {t("timeclock.staff.noShifts")}
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

// Valor/hora editable (Tanda D Finanzas): alimenta el labor cost real del
// Asesor. Se edita en pesos y se guarda en minor units; vacío borra el rate.
function HourlyRateCell({ userId, rate }: { userId: string; rate: number | null }) {
  const { t } = useTranslation()
  const setRate = useSetHourlyRate()
  const [value, setValue] = useState(rate != null ? String(rate / 100) : "")

  const save = () => {
    const trimmed = value.trim()
    const amount = trimmed === "" ? null : Math.round(Number(trimmed) * 100)
    if (trimmed !== "" && (!Number.isFinite(amount) || (amount as number) < 0)) {
      toast.error(t("timeclock.staff.invalidRate"))
      setValue(rate != null ? String(rate / 100) : "")
      return
    }
    if (amount === rate) return
    setRate.mutate(
      { userId, amount },
      {
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("timeclock.staff.rateError"))),
      }
    )
  }

  return (
    <Input
      type="number"
      min="0"
      step="0.01"
      inputMode="decimal"
      placeholder="—"
      aria-label={t("timeclock.staff.columns.hourlyRate")}
      className="ml-auto h-8 w-28 text-right tabular-nums"
      value={value}
      disabled={setRate.isPending}
      onChange={(e) => setValue(e.target.value)}
      onBlur={save}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.currentTarget.blur()
      }}
    />
  )
}
