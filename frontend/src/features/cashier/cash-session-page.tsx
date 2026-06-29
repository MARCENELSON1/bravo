import { Fragment, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { CashReportDTO, PaymentMethod } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useCloseCashSession,
  useCurrentCashSession,
  useOpenCashSession,
} from "@/hooks/use-cash"
import { formatMoney } from "@/lib/money"

const METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: "Efectivo",
  CARD: "Tarjeta",
  TRANSFER: "Transferencia",
  MERCADOPAGO: "MercadoPago",
  QR: "QR",
}

function signedMoney(amount: number, currency: string): string {
  const sign = amount < 0 ? "−" : amount > 0 ? "+" : ""
  return `${sign}${formatMoney(Math.abs(amount), currency)}`
}

export function CashSessionPage() {
  const session = useCurrentCashSession()
  const [closedReport, setClosedReport] = useState<CashReportDTO | null>(null)

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 px-6 py-8">
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
        <OpenSession report={session.data} onClosed={setClosedReport} />
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
        <div className="grid grid-cols-[1fr_auto_auto] items-center gap-x-3 gap-y-2 text-sm">
          <span className="text-xs font-medium text-muted-foreground">Medio</span>
          <span className="text-right text-xs font-medium text-muted-foreground">Esperado</span>
          <span className="text-right text-xs font-medium text-muted-foreground">Contado</span>
          {report.lines.map((line) => (
            <Row
              key={line.method}
              label={METHOD_LABELS[line.method]}
              expected={formatMoney(line.expected, report.currency)}
              value={counted[line.method] ?? ""}
              onChange={(v) => setMethod(line.method, v)}
            />
          ))}
        </div>
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
        <Button onClick={submit} disabled={close.isPending}>
          {close.isPending ? "Cerrando…" : "Cerrar caja"}
        </Button>
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
  expected: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <>
      <span>{label}</span>
      <span className="text-right tabular-nums text-muted-foreground">{expected}</span>
      <Input
        type="number"
        min={0}
        step="0.01"
        inputMode="decimal"
        placeholder="0.00"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-28 text-right"
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
        <div className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-x-3 gap-y-1 text-sm">
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
        </div>
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
