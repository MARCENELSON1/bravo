import { Fragment, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type {
  CashMovementKind,
  CashReportDTO,
  PaymentMethod,
} from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useCloseCashSession,
  useCurrentCashSession,
  useOpenCashSession,
  useRegisterCashMovement,
} from "@/hooks/use-cash"
import { formatMoney } from "@/lib/money"

const METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: "Efectivo",
  CARD: "Tarjeta",
  TRANSFER: "Transferencia",
  MERCADOPAGO: "MercadoPago",
  QR: "QR",
}

const MOVEMENT_KINDS: { kind: CashMovementKind; label: string }[] = [
  { kind: "DROP", label: "Sangría" },
  { kind: "DEPOSIT", label: "Ingreso" },
  { kind: "PAYOUT", label: "Pago" },
]

const MOVEMENT_LABELS: Record<CashMovementKind, string> = {
  DROP: "Sangría",
  DEPOSIT: "Ingreso de efectivo",
  PAYOUT: "Pago en efectivo",
}

function signedMoney(amount: number, currency: string): string {
  const sign = amount < 0 ? "−" : amount > 0 ? "+" : ""
  return `${sign}${formatMoney(Math.abs(amount), currency)}`
}

export function CashSessionPage() {
  const session = useCurrentCashSession()
  const [closedReport, setClosedReport] = useState<CashReportDTO | null>(null)

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Caja
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          Apertura con fondo, arqueo Z (esperado vs contado) y cierre de turno.
        </p>
      </header>

      {session.isPending ? (
        <Spinner />
      ) : closedReport ? (
        <ClosedArqueo report={closedReport} onDone={() => setClosedReport(null)} />
      ) : session.data ? (
        <>
          <OpenSession report={session.data} onClosed={setClosedReport} />
          <CashMovements report={session.data} />
        </>
      ) : (
        <OpenForm />
      )}
    </div>
  )
}

function OpenForm() {
  const open = useOpenCashSession()
  const [amount, setAmount] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount || 0) * 100)
    if (!Number.isFinite(minor) || minor < 0) {
      toast.error("Ingresá un fondo válido.")
      return
    }
    open.mutate(
      { amount: minor },
      {
        onSuccess: () => toast.success("Caja abierta."),
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos abrir la caja."),
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Abrir caja</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <label className="text-sm text-muted-foreground" htmlFor="float">
          Fondo inicial (efectivo en la caja)
        </label>
        <div className="flex items-center gap-2">
          <Input
            id="float"
            type="number"
            min={0}
            step="0.01"
            inputMode="decimal"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="max-w-[10rem]"
          />
          <Button onClick={submit} disabled={open.isPending}>
            {open.isPending ? "Abriendo…" : "Abrir caja"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function OpenSession({
  report,
  onClosed,
}: {
  report: CashReportDTO
  onClosed: (report: CashReportDTO) => void
}) {
  const close = useCloseCashSession()
  // Counted amount (pesos as typed) per method.
  const [counted, setCounted] = useState<Partial<Record<PaymentMethod, string>>>({})

  const setMethod = (method: PaymentMethod, value: string) =>
    setCounted((prev) => ({ ...prev, [method]: value }))

  const submit = () => {
    const payload: Partial<Record<PaymentMethod, number>> = {}
    for (const line of report.lines) {
      const raw = counted[line.method]
      payload[line.method] = Math.round(Number(raw || 0) * 100)
    }
    close.mutate(
      { sessionId: report.session_id, counted: payload },
      {
        onSuccess: (final) => {
          toast.success("Caja cerrada.")
          onClosed(final)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos cerrar la caja."),
      }
    )
  }

  const blind = report.blind
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Arqueo Z</span>
          <span className="text-xs font-normal text-muted-foreground">
            Fondo {formatMoney(report.opening_float, report.currency)}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {blind ? (
          <p className="rounded-md border border-primary/40 bg-primary/5 px-3 py-2 text-xs text-muted-foreground">
            Arqueo ciego: contá sin ver el esperado. La diferencia se revela al cerrar.
          </p>
        ) : null}
        <div
          className={
            "grid items-center gap-x-3 gap-y-2 text-sm " +
            (blind ? "grid-cols-[1fr_auto]" : "grid-cols-[1fr_auto_auto]")
          }
        >
          <span className="text-xs font-medium text-muted-foreground">Medio</span>
          {blind ? null : (
            <span className="text-right text-xs font-medium text-muted-foreground">Esperado</span>
          )}
          <span className="text-right text-xs font-medium text-muted-foreground">Contado</span>
          {report.lines.map((line) => (
            <Row
              key={line.method}
              label={METHOD_LABELS[line.method]}
              expected={blind ? null : formatMoney(line.expected, report.currency)}
              value={counted[line.method] ?? ""}
              onChange={(v) => setMethod(line.method, v)}
            />
          ))}
        </div>
        {blind ? null : (
          <>
            <div className="flex items-center justify-between border-t pt-3 text-sm font-medium">
              <span>Esperado total</span>
              <span>{formatMoney(report.expected_total, report.currency)}</span>
            </div>
            {report.tips_total > 0 ? (
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Propinas (incluidas; para repartir)</span>
                <span>{formatMoney(report.tips_total, report.currency)}</span>
              </div>
            ) : null}
          </>
        )}
        <Button onClick={submit} disabled={close.isPending}>
          {close.isPending ? "Cerrando…" : "Cerrar caja"}
        </Button>
      </CardContent>
    </Card>
  )
}

function CashMovements({ report }: { report: CashReportDTO }) {
  const register = useRegisterCashMovement()
  const [kind, setKind] = useState<CashMovementKind>("DROP")
  const [amount, setAmount] = useState("")
  const [reason, setReason] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount || 0) * 100)
    if (!Number.isFinite(minor) || minor <= 0) {
      toast.error("Ingresá un monto válido.")
      return
    }
    register.mutate(
      { kind, amount: minor, reason: reason.trim() || null },
      {
        onSuccess: () => {
          toast.success("Movimiento registrado.")
          setAmount("")
          setReason("")
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar el movimiento."),
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Movimientos de caja</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-xs text-muted-foreground">
          Sangrías, ingresos de efectivo y pagos desde el cajón. Ajustan el esperado del arqueo
          (no son ventas ni egresos del resultado).
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {MOVEMENT_KINDS.map((m) => (
            <Button
              key={m.kind}
              size="sm"
              variant={kind === m.kind ? "default" : "outline"}
              onClick={() => setKind(m.kind)}
            >
              {m.label}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            type="number"
            min={0}
            step="0.01"
            inputMode="decimal"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="max-w-[9rem]"
          />
          <Input
            placeholder="Motivo (opcional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="max-w-[14rem] flex-1"
          />
          <Button onClick={submit} disabled={register.isPending}>
            Registrar
          </Button>
        </div>

        {report.movements.length > 0 ? (
          <div className="flex flex-col gap-1 border-t pt-3">
            {report.movements.map((mv) => (
              <div key={mv.id} className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate">
                  {MOVEMENT_LABELS[mv.kind]}
                  {mv.reason ? (
                    <span className="text-muted-foreground"> · {mv.reason}</span>
                  ) : null}
                </span>
                <span
                  className={
                    "shrink-0 tabular-nums " +
                    (mv.signed_amount < 0 ? "text-red-600" : "text-emerald-600")
                  }
                >
                  {signedMoney(mv.signed_amount, report.currency)}
                </span>
              </div>
            ))}
            <div className="mt-1 flex items-center justify-between border-t pt-2 text-xs text-muted-foreground">
              <span>
                Ingresos {formatMoney(report.cash_in_total, report.currency)} · Salidas{" "}
                {formatMoney(report.cash_out_total, report.currency)}
              </span>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

function Row({
  label,
  expected,
  value,
  onChange,
}: {
  label: string
  expected: string | null
  value: string
  onChange: (value: string) => void
}) {
  return (
    <>
      <span>{label}</span>
      {expected !== null ? (
        <span className="text-right tabular-nums text-muted-foreground">{expected}</span>
      ) : null}
      <Input
        type="number"
        min={0}
        step="0.01"
        inputMode="decimal"
        placeholder="0.00"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-20 text-right sm:w-28"
      />
    </>
  )
}

function ClosedArqueo({
  report,
  onDone,
}: {
  report: CashReportDTO
  onDone: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Caja cerrada · arqueo</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="overflow-x-auto"><div className="grid min-w-[26rem] grid-cols-[1fr_auto_auto_auto] items-center gap-x-3 gap-y-1 text-sm">
          <span className="text-xs font-medium text-muted-foreground">Medio</span>
          <span className="text-right text-xs font-medium text-muted-foreground">Esperado</span>
          <span className="text-right text-xs font-medium text-muted-foreground">Contado</span>
          <span className="text-right text-xs font-medium text-muted-foreground">Dif.</span>
          {report.lines.map((line) => (
            <Fragment key={line.method}>
              <span>{METHOD_LABELS[line.method]}</span>
              <span className="text-right tabular-nums">
                {formatMoney(line.expected, report.currency)}
              </span>
              <span className="text-right tabular-nums">
                {formatMoney(line.counted ?? 0, report.currency)}
              </span>
              <span
                className={
                  "text-right tabular-nums " +
                  ((line.difference ?? 0) < 0
                    ? "text-red-600"
                    : (line.difference ?? 0) > 0
                      ? "text-amber-600"
                      : "text-muted-foreground")
                }
              >
                {signedMoney(line.difference ?? 0, report.currency)}
              </span>
            </Fragment>
          ))}
        </div></div>
        <div className="flex items-center justify-between border-t pt-3 text-sm font-medium">
          <span>Diferencia total</span>
          <span
            className={
              (report.difference_total ?? 0) < 0
                ? "text-red-600"
                : (report.difference_total ?? 0) > 0
                  ? "text-amber-600"
                  : ""
            }
          >
            {signedMoney(report.difference_total ?? 0, report.currency)}
          </span>
        </div>
        {report.tips_total > 0 ? (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Propinas (incluidas; para repartir)</span>
            <span>{formatMoney(report.tips_total, report.currency)}</span>
          </div>
        ) : null}
        <Button variant="outline" onClick={onDone}>
          Listo
        </Button>
      </CardContent>
    </Card>
  )
}
