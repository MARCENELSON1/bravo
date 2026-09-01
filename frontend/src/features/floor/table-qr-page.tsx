import { ArrowLeft, Printer } from "lucide-react"
import { QRCodeSVG } from "qrcode.react"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router-dom"

import type { TableDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useTableQr, useTables } from "@/hooks/use-tables"

// Gestión/impresión de los QR de mesa (lado dueño, OWNER/MANAGER). Pantalla
// completa (fuera del shell) para imprimir limpio: la barra superior se oculta al
// imprimir (`print:hidden`) y cada QR queda en su tarjeta, una por mesa.
export function TableQrPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const tables = useTables()
  const active = (tables.data ?? []).filter((table) => table.active)

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-border/60 bg-background/80 px-5 py-4 backdrop-blur-xl print:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(-1)}
          aria-label={t("floor.qr.back")}
        >
          <ArrowLeft className="size-4" />
        </Button>
        <div className="min-w-0 flex-1">
          <h1 className="text-lg font-semibold leading-tight">{t("floor.qr.title")}</h1>
          <p className="truncate text-xs text-muted-foreground">{t("floor.qr.subtitle")}</p>
        </div>
        {active.length > 0 ? (
          <Button onClick={() => window.print()}>
            <Printer className="mr-2 size-4" />
            {t("floor.qr.print")}
          </Button>
        ) : null}
      </header>

      <main className="mx-auto max-w-4xl px-5 py-8">
        {tables.isLoading ? (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        ) : active.length === 0 ? (
          <p className="py-20 text-center text-sm text-muted-foreground">{t("floor.qr.empty")}</p>
        ) : (
          <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 print:grid-cols-2">
            {active.map((table) => (
              <TableQrCard key={table.id} table={table} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

function TableQrCard({ table }: { table: TableDTO }) {
  const { t } = useTranslation()
  const qr = useTableQr(table.id)

  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-border/60 bg-card p-6 text-center print:break-inside-avoid">
      <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {t("floor.qr.tableLabel", { number: table.number })}
      </p>
      {qr.isLoading ? (
        <div className="flex h-[204px] items-center justify-center">
          <Spinner />
        </div>
      ) : qr.data ? (
        <>
          {/* Fondo blanco SIEMPRE (aunque el tema sea oscuro) para que escanee. */}
          <div className="rounded-xl bg-white p-3">
            <QRCodeSVG value={qr.data.url} size={180} />
          </div>
          <p className="text-xs text-muted-foreground">{t("floor.qr.scanHint")}</p>
        </>
      ) : (
        <p className="flex h-[204px] items-center text-xs text-destructive">
          {t("floor.qr.loadError")}
        </p>
      )}
    </div>
  )
}
