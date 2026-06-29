import { Fragment } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
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
  const report = useTipsReport()

  return (
    <div className="flex flex-col gap-4">
      <GradientHeading>Propinas</GradientHeading>
      {report.isLoading ? (
        <Spinner />
      ) : report.data ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Por mozo</span>
              <span className="text-sm font-normal text-muted-foreground">
                Pendiente: {formatMoney(report.data.pending_total, report.data.currency)}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {report.data.rows.length === 0 ? (
              <p className="text-sm text-muted-foreground">Todavía no hay propinas registradas.</p>
            ) : (
              <div className="grid grid-cols-[1fr_auto_auto_auto_auto] items-center gap-x-3 gap-y-2 text-sm">
                <span className="text-xs font-medium text-muted-foreground">Mozo</span>
                <span className="text-right text-xs font-medium text-muted-foreground">Ganó</span>
                <span className="text-right text-xs font-medium text-muted-foreground">Pagado</span>
                <span className="text-right text-xs font-medium text-muted-foreground">
                  Pendiente
                </span>
                <span />
                {report.data.rows.map((row) => (
                  <TipRow key={row.waiter_id} row={row} currency={report.data!.currency} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground">No pudimos cargar las propinas.</p>
      )}
    </div>
  )
}

function TipRow({ row, currency }: { row: TipsReportRowDTO; currency: string }) {
  const payTip = usePayTip()
  const canPay = row.pending > 0

  const liquidar = () => {
    if (!window.confirm(`¿Liquidar ${formatMoney(row.pending, currency)} a ${row.waiter_email}?`)) {
      return
    }
    payTip.mutate(
      { waiterId: row.waiter_id, amount: row.pending },
      {
        onSuccess: () => toast.success("Propina liquidada."),
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos liquidar la propina."),
      }
    )
  }

  return (
    <Fragment>
      <span className="truncate">{row.waiter_email}</span>
      <span className="text-right tabular-nums">{formatMoney(row.earned, currency)}</span>
      <span className="text-right tabular-nums text-muted-foreground">
        {formatMoney(row.paid, currency)}
      </span>
      <span className="text-right tabular-nums font-medium">
        {formatMoney(row.pending, currency)}
      </span>
      <Button size="sm" variant="outline" onClick={liquidar} disabled={!canPay || payTip.isPending}>
        Liquidar
      </Button>
    </Fragment>
  )
}
