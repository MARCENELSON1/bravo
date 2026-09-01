import { Fragment, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
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

const MOVEMENT_KINDS: CashMovementKind[] = ["DROP", "DEPOSIT", "PAYOUT"]

function signedMoney(amount: number, currency: string): string {
  const sign = amount < 0 ? "−" : amount > 0 ? "+" : ""
  return `${sign}${formatMoney(Math.abs(amount), currency)}`
}

export function CashSessionPage() {
  const { t } = useTranslation()
  const session = useCurrentCashSession()
  const [closedReport, setClosedReport] = useState<CashReportDTO | null>(null)

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {t("cashier.title")}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          {t("cashier.subtitle")}
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
  const { t } = useTranslation()
  const open = useOpenCashSession()
  const [amount, setAmount] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount || 0) * 100)
    if (!Number.isFinite(minor) || minor < 0) {
      toast.error(t("cashier.open.invalidFloat"))
      return
    }
    open.mutate(
      { amount: minor },
      {
        onSuccess: () => toast.success(t("cashier.open.success")),
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("cashier.open.error"))),
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("cashier.open.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <label className="text-sm text-muted-foreground" htmlFor="float">
          {t("cashier.open.floatLabel")}
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
            {open.isPending ? t("cashier.open.submitting") : t("cashier.open.submit")}
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
  const { t } = useTranslation()
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
          toast.success(t("cashier.reconcile.success"))
          onClosed(final)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("cashier.reconcile.error"))),
      }
    )
  }

  const blind = report.blind
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{t("cashier.reconcile.title")}</span>
          <span className="text-xs font-normal text-muted-foreground">
            {t("cashier.reconcile.float", {
              amount: formatMoney(report.opening_float, report.currency),
            })}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {blind ? (
          <p className="rounded-md border border-primary/40 bg-primary/5 px-3 py-2 text-xs text-muted-foreground">
            {t("cashier.reconcile.blindNotice")}
          </p>
        ) : null}
        <div
          className={
            "grid items-center gap-x-3 gap-y-2 text-sm " +
            (blind ? "grid-cols-[1fr_auto]" : "grid-cols-[1fr_auto_auto]")
          }
        >
          <span className="text-xs font-medium text-muted-foreground">{t("cashier.reconcile.method")}</span>
          {blind ? null : (
            <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.reconcile.expected")}</span>
          )}
          <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.reconcile.counted")}</span>
          {report.lines.map((line) => (
            <Row
              key={line.method}
              label={t(`cashier.methodLabels.${line.method}`)}
              expected={blind ? null : formatMoney(line.expected, report.currency)}
              value={counted[line.method] ?? ""}
              onChange={(v) => setMethod(line.method, v)}
            />
          ))}
        </div>
        {blind ? null : (
          <>
            <div className="flex items-center justify-between border-t pt-3 text-sm font-medium">
              <span>{t("cashier.reconcile.expectedTotal")}</span>
              <span>{formatMoney(report.expected_total, report.currency)}</span>
            </div>
            {report.tips_total > 0 ? (
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{t("cashier.reconcile.tips")}</span>
                <span>{formatMoney(report.tips_total, report.currency)}</span>
              </div>
            ) : null}
          </>
        )}
        <Button onClick={submit} disabled={close.isPending}>
          {close.isPending ? t("cashier.reconcile.submitting") : t("cashier.reconcile.submit")}
        </Button>
      </CardContent>
    </Card>
  )
}

function CashMovements({ report }: { report: CashReportDTO }) {
  const { t } = useTranslation()
  const register = useRegisterCashMovement()
  const [kind, setKind] = useState<CashMovementKind>("DROP")
  const [amount, setAmount] = useState("")
  const [reason, setReason] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount || 0) * 100)
    if (!Number.isFinite(minor) || minor <= 0) {
      toast.error(t("cashier.movements.invalidAmount"))
      return
    }
    register.mutate(
      { kind, amount: minor, reason: reason.trim() || null },
      {
        onSuccess: () => {
          toast.success(t("cashier.movements.success"))
          setAmount("")
          setReason("")
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("cashier.movements.error"))),
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("cashier.movements.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-xs text-muted-foreground">
          {t("cashier.movements.hint")}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {MOVEMENT_KINDS.map((m) => (
            <Button
              key={m}
              size="sm"
              variant={kind === m ? "default" : "outline"}
              onClick={() => setKind(m)}
            >
              {t(`cashier.movementKinds.${m}`)}
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
            placeholder={t("cashier.movements.reasonPlaceholder")}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="max-w-[14rem] flex-1"
          />
          <Button onClick={submit} disabled={register.isPending}>
            {t("cashier.movements.submit")}
          </Button>
        </div>

        {report.movements.length > 0 ? (
          <div className="flex flex-col gap-1 border-t pt-3">
            {report.movements.map((mv) => (
              <div key={mv.id} className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate">
                  {t(`cashier.movementLabels.${mv.kind}`)}
                  {mv.reason ? (
                    <span className="text-muted-foreground"> · {mv.reason}</span>
                  ) : null}
                </span>
                <span
                  className={
                    "shrink-0 tabular-nums " +
                    (mv.signed_amount < 0 ? "text-destructive" : "text-success")
                  }
                >
                  {signedMoney(mv.signed_amount, report.currency)}
                </span>
              </div>
            ))}
            <div className="mt-1 flex items-center justify-between border-t pt-2 text-xs text-muted-foreground">
              <span>
                {t("cashier.movements.cashInOut", {
                  cashIn: formatMoney(report.cash_in_total, report.currency),
                  cashOut: formatMoney(report.cash_out_total, report.currency),
                })}
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
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("cashier.closed.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="overflow-x-auto"><div className="grid min-w-[26rem] grid-cols-[1fr_auto_auto_auto] items-center gap-x-3 gap-y-1 text-sm">
          <span className="text-xs font-medium text-muted-foreground">{t("cashier.closed.method")}</span>
          <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.closed.expected")}</span>
          <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.closed.counted")}</span>
          <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.closed.difference")}</span>
          {report.lines.map((line) => (
            <Fragment key={line.method}>
              <span>{t(`cashier.methodLabels.${line.method}`)}</span>
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
                    ? "text-destructive"
                    : (line.difference ?? 0) > 0
                      ? "text-warning"
                      : "text-muted-foreground")
                }
              >
                {signedMoney(line.difference ?? 0, report.currency)}
              </span>
            </Fragment>
          ))}
        </div></div>
        <div className="flex items-center justify-between border-t pt-3 text-sm font-medium">
          <span>{t("cashier.closed.differenceTotal")}</span>
          <span
            className={
              (report.difference_total ?? 0) < 0
                ? "text-destructive"
                : (report.difference_total ?? 0) > 0
                  ? "text-warning"
                  : ""
            }
          >
            {signedMoney(report.difference_total ?? 0, report.currency)}
          </span>
        </div>
        {report.tips_total > 0 ? (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{t("cashier.closed.tips")}</span>
            <span>{formatMoney(report.tips_total, report.currency)}</span>
          </div>
        ) : null}
        <Button variant="outline" onClick={onDone}>
          {t("cashier.closed.done")}
        </Button>
      </CardContent>
    </Card>
  )
}
