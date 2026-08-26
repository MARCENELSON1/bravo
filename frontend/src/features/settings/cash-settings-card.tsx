import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { CashSettingsDTO } from "@/api/types-operations"
import { Spinner } from "@/components/ui/spinner"
import { useCashSettings, useUpdateCashSettings } from "@/hooks/use-cash"
import { cn } from "@/lib/utils"

function Toggle({
  checked,
  disabled,
  onChange,
}: {
  checked: boolean
  disabled?: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors",
        checked ? "bg-primary" : "bg-black/15 dark:bg-white/25",
        disabled ? "cursor-not-allowed opacity-70" : "cursor-pointer"
      )}
    >
      <span
        className={cn(
          "inline-block size-5 rounded-full bg-white shadow ring-1 ring-black/10 transition-transform",
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        )}
      />
    </button>
  )
}

// Config → Caja y pagos: los dos flags de política de caja (exigir caja abierta
// para cobrar + arqueo ciego). OFF por default. Editable por OWNER/MANAGER.
export function CashSettingsCard() {
  const { t } = useTranslation()
  const settings = useCashSettings()
  const update = useUpdateCashSettings()

  const set = (patch: Partial<CashSettingsDTO>) => {
    const base = settings.data
    if (!base) return
    update.mutate(
      { ...base, ...patch },
      {
        onError: (e) =>
          toast.error(apiErrorText(e, t, t("settings.cash.saveError"))),
      }
    )
  }

  if (settings.isPending) return <Spinner />
  const data = settings.data
  if (!data) return null

  return (
    <div className="flex flex-col divide-y divide-border">
      <div className="flex items-center justify-between gap-4 py-4">
        <div>
          <p className="text-sm font-medium text-foreground">
            {t("settings.cash.requireOpenTitle")}
          </p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {t("settings.cash.requireOpenDesc")}
          </p>
        </div>
        <Toggle
          checked={data.require_open_cash_session}
          disabled={update.isPending}
          onChange={(v) => set({ require_open_cash_session: v })}
        />
      </div>
      <div className="flex items-center justify-between gap-4 py-4">
        <div>
          <p className="text-sm font-medium text-foreground">{t("settings.cash.blindTitle")}</p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {t("settings.cash.blindDesc")}
          </p>
        </div>
        <Toggle
          checked={data.blind_cash_count}
          disabled={update.isPending}
          onChange={(v) => set({ blind_cash_count: v })}
        />
      </div>
    </div>
  )
}
