import { Fragment } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { TipsReportRowDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { usePayTip, useTipsReport } from "@/hooks/use-cash"
import { formatMoney } from "@/lib/money"

// "Propinas por mozo": cuánto ganó cada uno (atribuido por la orden) vs cuánto se
// le liquidó (egreso 'Propinas'). El pago se registra como egreso → baja la caja.
export function TipsPage() {
  const { t } = useTranslation()
  const report = useTipsReport()

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <GradientHeading>{t("cashier.tips.title")}</GradientHeading>
      {report.isLoading ? (
        <Spinner />
      ) : report.data ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{t("cashier.tips.byWaiter")}</span>
              <span className="text-sm font-normal text-muted-foreground">
                {t("cashier.tips.pendingTotal", {
                  amount: formatMoney(report.data.pending_total, report.data.currency),
                })}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {report.data.rows.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("cashier.tips.empty")}</p>
            ) : (
              <div className="overflow-x-auto"><div className="grid min-w-[30rem] grid-cols-[1fr_auto_auto_auto_auto] items-center gap-x-3 gap-y-2 text-sm">
                <span className="text-xs font-medium text-muted-foreground">{t("cashier.tips.waiter")}</span>
                <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.tips.earned")}</span>
                <span className="text-right text-xs font-medium text-muted-foreground">{t("cashier.tips.paid")}</span>
                <span className="text-right text-xs font-medium text-muted-foreground">
                  {t("cashier.tips.pending")}
                </span>
                <span />
                {report.data.rows.map((row) => (
                  <TipRow key={row.waiter_id} row={row} currency={report.data!.currency} />
                ))}
              </div></div>
            )}
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground">{t("cashier.tips.loadError")}</p>
      )}
    </div>
  )
}

function TipRow({ row, currency }: { row: TipsReportRowDTO; currency: string }) {
  const { t } = useTranslation()
  const payTip = usePayTip()
  const canPay = row.pending > 0

  const liquidar = () => {
    if (
      !window.confirm(
        t("cashier.tips.confirm", {
          amount: formatMoney(row.pending, currency),
          name: row.waiter_name,
        })
      )
    ) {
      return
    }
    payTip.mutate(
      { waiterId: row.waiter_id, amount: row.pending },
      {
        onSuccess: () => toast.success(t("cashier.tips.paySuccess")),
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("cashier.tips.payError"))),
      }
    )
  }

  return (
    <Fragment>
      <span className="truncate">{row.waiter_name}</span>
      <span className="text-right tabular-nums">{formatMoney(row.earned, currency)}</span>
      <span className="text-right tabular-nums text-muted-foreground">
        {formatMoney(row.paid, currency)}
      </span>
      <span className="text-right tabular-nums font-medium">
        {formatMoney(row.pending, currency)}
      </span>
      <Button size="sm" variant="outline" onClick={liquidar} disabled={!canPay || payTip.isPending}>
        {t("cashier.tips.pay")}
      </Button>
    </Fragment>
  )
}
