import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { FeeRateDTO, PaymentMethod } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useFeeRates, useUpdateFeeRates } from "@/hooks/use-fee-rates"

// Comisiones (slice B): cargá lo que se queda la pasarela por cada medio → el
// Inicio muestra la ganancia REAL (neta de comisiones). Medios electrónicos; el
// efectivo/transferencia no tienen comisión de pasarela.
const METHODS: PaymentMethod[] = ["CARD", "MERCADOPAGO", "QR"]

export function CommissionRatesCard() {
  const rates = useFeeRates()
  if (rates.isPending) {
    return (
      <GlassCard className="flex justify-center p-6">
        <Spinner className="size-5 text-muted-foreground" />
      </GlassCard>
    )
  }
  return <CommissionRatesForm initial={rates.data?.rates ?? []} />
}

function CommissionRatesForm({ initial }: { initial: FeeRateDTO[] }) {
  const { t } = useTranslation()
  const update = useUpdateFeeRates()
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      METHODS.map((method) => {
        const r = initial.find((x) => x.method === method)
        return [method, r && r.fee_bps ? String(r.fee_bps / 100) : ""]
      }),
    ),
  )

  const save = () => {
    const payload: FeeRateDTO[] = []
    for (const method of METHODS) {
      const raw = (values[method] ?? "").trim()
      const pct = raw ? Number(raw) : 0
      if (!Number.isFinite(pct) || pct < 0 || pct > 100) {
        toast.error(t("finance.commissionRates.invalid"))
        return
      }
      payload.push({ method, fee_bps: Math.round(pct * 100) })
    }
    update.mutate(payload, {
      onSuccess: () => toast.success(t("finance.commissionRates.saved")),
      onError: (e) =>
        toast.error(apiErrorText(e, t, t("finance.commissionRates.saveError"))),
    })
  }

  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <div>
        <h2 className="text-base font-semibold text-foreground">
          {t("finance.commissionRates.title")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("finance.commissionRates.descPre")}{" "}
          <em>{t("finance.commissionRates.descEm")}</em>{" "}
          {t("finance.commissionRates.descPost")}
        </p>
      </div>
      {METHODS.map((method) => (
        <label key={method} className="flex items-center justify-between gap-2 text-sm">
          <span className="text-foreground">{t(`finance.paymentMethods.${method}`)}</span>
          <span className="flex items-center gap-1">
            <Input
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={values[method]}
              onChange={(e) => setValues((v) => ({ ...v, [method]: e.target.value }))}
              className="w-24 text-right"
              placeholder="0"
            />
            <span className="text-muted-foreground">%</span>
          </span>
        </label>
      ))}
      <Button onClick={save} disabled={update.isPending} className="self-start">
        {update.isPending ? t("finance.commissionRates.saving") : t("finance.commissionRates.save")}
      </Button>
    </GlassCard>
  )
}
