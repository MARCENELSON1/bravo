import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { ReportExportKind } from "@/api/reports-api"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { saveBlob } from "@/lib/download"
import { type RangeWindow } from "@/lib/finance-range"
import { useServices } from "@/services/services-context"

const EXPORTS: { kind: ReportExportKind; label: string; filename: string }[] = [
  { kind: "sales", label: "Ventas (CSV)", filename: "ventas-por-dia.csv" },
  { kind: "expenses", label: "Gastos (CSV)", filename: "gastos.csv" },
  { kind: "vat_sales", label: "Libro IVA Ventas (CSV)", filename: "libro-iva-ventas.csv" },
]

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
  const exportCsv = useExportCsv()

  const run = (kind: ReportExportKind, filename: string) =>
    exportCsv.mutate(
      { kind, from: window.from, to: window.to, filename },
      {
        onError: (e) =>
          toast.error(isApiError(e) ? e.message : "No pudimos generar el archivo."),
      }
    )

  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <div>
        <h2 className="text-base font-semibold text-foreground">Exportar para el contador</h2>
        <p className="text-sm text-muted-foreground">
          Descargá los datos del período en CSV (apto Excel). Se abre con acentos y separado por
          punto y coma.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {EXPORTS.map((e) => (
          <Button
            key={e.kind}
            variant="outline"
            disabled={exportCsv.isPending}
            onClick={() => run(e.kind, e.filename)}
          >
            {e.label}
          </Button>
        ))}
      </div>
    </GlassCard>
  )
}
