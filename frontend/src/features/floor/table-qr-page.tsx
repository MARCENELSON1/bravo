import { ArrowLeft, Printer } from "lucide-react"
import { QRCodeSVG } from "qrcode.react"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import type { TableDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useSelfOrderSettings, useUpdateSelfOrderSettings } from "@/hooks/use-self-order"
import { useSelfPaySettings, useUpdateSelfPaySettings } from "@/hooks/use-self-pay"
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
        <div className="mb-8 grid gap-5 print:hidden md:grid-cols-2">
          <SelfOrderConfigCard />
          <SelfPayConfigCard />
        </div>
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

// Config del autopedido (Carta QR F2 E): prender el autopedido + el gate de
// confirmación del mozo. Sin autopedido, la carta QR queda de solo lectura (F1).
function SelfOrderConfigCard() {
  const { t } = useTranslation()
  const settings = useSelfOrderSettings()
  const update = useUpdateSelfOrderSettings()

  const save = (next: { enabled: boolean; requires_confirmation: boolean }) =>
    update.mutate(next, {
      onSuccess: () => toast.success(t("floor.qr.selfOrder.saved")),
      onError: () => toast.error(t("floor.qr.selfOrder.saveFailed")),
    })

  const current = settings.data
  const enabled = current?.enabled ?? false
  const requiresConfirmation = current?.requires_confirmation ?? true

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-5">
      <h2 className="text-sm font-semibold">{t("floor.qr.selfOrder.title")}</h2>
      <p className="mt-0.5 text-xs text-muted-foreground">{t("floor.qr.selfOrder.subtitle")}</p>
      {settings.isLoading ? (
        <div className="py-4">
          <Spinner className="size-4" />
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={enabled}
              disabled={update.isPending}
              onChange={(e) =>
                save({ enabled: e.target.checked, requires_confirmation: requiresConfirmation })
              }
            />
            <span className="text-sm">{t("floor.qr.selfOrder.enable")}</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-0.5 size-4 accent-primary"
              checked={requiresConfirmation}
              disabled={!enabled || update.isPending}
              onChange={(e) =>
                save({ enabled, requires_confirmation: e.target.checked })
              }
            />
            <span className={enabled ? "text-sm" : "text-sm text-muted-foreground"}>
              {t("floor.qr.selfOrder.requireConfirmation")}
              <span className="mt-0.5 block text-xs text-muted-foreground">
                {t("floor.qr.selfOrder.requireConfirmationHint")}
              </span>
            </span>
          </label>
        </div>
      )}
    </div>
  )
}

// Config del pago desde la mesa (Carta QR F3 C): prender el cobro online del
// comensal + decidir si la pantalla de pago ofrece propina. Off por default →
// la carta mantiene "Pedir la cuenta" (paridad F1/F2).
function SelfPayConfigCard() {
  const { t } = useTranslation()
  const settings = useSelfPaySettings()
  const update = useUpdateSelfPaySettings()

  const save = (next: { enabled: boolean; tips_enabled: boolean }) =>
    update.mutate(next, {
      onSuccess: () => toast.success(t("floor.qr.selfPay.saved")),
      onError: () => toast.error(t("floor.qr.selfPay.saveFailed")),
    })

  const current = settings.data
  const enabled = current?.enabled ?? false
  const tipsEnabled = current?.tips_enabled ?? true

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-5">
      <h2 className="text-sm font-semibold">{t("floor.qr.selfPay.title")}</h2>
      <p className="mt-0.5 text-xs text-muted-foreground">{t("floor.qr.selfPay.subtitle")}</p>
      {settings.isLoading ? (
        <div className="py-4">
          <Spinner className="size-4" />
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-0.5 size-4 accent-primary"
              checked={enabled}
              disabled={update.isPending}
              onChange={(e) => save({ enabled: e.target.checked, tips_enabled: tipsEnabled })}
            />
            <span className="text-sm">
              {t("floor.qr.selfPay.enable")}
              <span className="mt-0.5 block text-xs text-muted-foreground">
                {t("floor.qr.selfPay.enableHint")}
              </span>
            </span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={tipsEnabled}
              disabled={!enabled || update.isPending}
              onChange={(e) => save({ enabled, tips_enabled: e.target.checked })}
            />
            <span className={enabled ? "text-sm" : "text-sm text-muted-foreground"}>
              {t("floor.qr.selfPay.offerTip")}
            </span>
          </label>
        </div>
      )}
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
