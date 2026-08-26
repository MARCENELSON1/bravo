import { useMutation } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import type { ReportExportKind } from "@/api/reports-api"
import { apiErrorText } from "@/api/translate-error"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { saveBlob } from "@/lib/download"
import { type RangeWindow } from "@/lib/finance-range"
import { useServices } from "@/services/services-context"

const EXPORT_KINDS: ReportExportKind[] = ["sales", "expenses", "vat_sales"]

function useExportCsv() {
  const { reportsApi } = useServices()
  return useMutation({
    mutationFn: async (vars: {
      kind: ReportExportKind
      from?: string
      to?: string
      filename: string
    }) => {
      const { blob, filename } = await reportsApi.exportCsv(vars.kind, {
        from: vars.from,
        to: vars.to,
      })
      saveBlob(blob, filename ?? vars.filename)
    },
  })
}

// Fase 10: 3 descargas CSV del período para pasarle al contador. Usa la ventana
// (period) de la pantalla que la monta.
export function AccountantExport({ window }: { window: RangeWindow }) {
  const { t } = useTranslation()
  const exportCsv = useExportCsv()

  const run = (kind: ReportExportKind) =>
    exportCsv.mutate(
      {
        kind,
        from: window.from,
        to: window.to,
        filename: t(`finance.exports.items.${kind}.filename`),
      },
      {
        onError: (e) => toast.error(apiErrorText(e, t, t("finance.exports.error"))),
      }
    )

  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <div>
        <h2 className="text-base font-semibold text-foreground">{t("finance.exports.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("finance.exports.description")}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {EXPORT_KINDS.map((kind) => (
          <Button
            key={kind}
            variant="outline"
            disabled={exportCsv.isPending}
            onClick={() => run(kind)}
          >
            {t(`finance.exports.items.${kind}.label`)}
          </Button>
        ))}
      </div>
    </GlassCard>
  )
}
