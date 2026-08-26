import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { FiscalSettingsDTO } from "@/api/types-tenant"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useFiscalSettings, useUpdateFiscalAddress } from "@/hooks/use-tenant"

// The form owns its state, seeded once from the loaded settings (no effect sync).
function AddressForm({ settings }: { settings: FiscalSettingsDTO }) {
  const { t } = useTranslation()
  const update = useUpdateFiscalAddress()
  const [street, setStreet] = useState(settings.street ?? "")
  const [city, setCity] = useState(settings.city ?? "")
  const [state, setState] = useState(settings.state ?? "")
  const [zip, setZip] = useState(settings.zip ?? "")

  const usesAddress = settings.tax_engine !== "NONE"

  const save = () => {
    update.mutate(
      {
        street: street.trim() || null,
        city: city.trim() || null,
        state: state.trim() || null,
        zip: zip.trim() || null,
      },
      {
        onSuccess: () => toast.success(t("settings.fiscal.saved")),
        onError: (e) =>
          toast.error(apiErrorText(e, t, t("settings.fiscal.saveError"))),
      }
    )
  }

  return (
    <div className="flex flex-col gap-4 py-4">
      <div>
        <p className="text-sm font-medium text-foreground">{t("settings.fiscal.title")}</p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {usesAddress
            ? t("settings.fiscal.descUsed")
            : t("settings.fiscal.descUnused")}
        </p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            {t(`settings.fiscal.regimeLabels.${settings.tax_regime}`, {
              defaultValue: settings.tax_regime,
            })}
          </span>
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            {t("settings.fiscal.taxesLabel")}:{" "}
            {t(`settings.fiscal.engineLabels.${settings.tax_engine}`, {
              defaultValue: settings.tax_engine,
            })}
          </span>
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            {settings.currency}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Input
          placeholder={t("settings.fiscal.street")}
          value={street}
          onChange={(e) => setStreet(e.target.value)}
        />
        <Input
          placeholder={t("settings.fiscal.city")}
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />
        <Input
          placeholder={t("settings.fiscal.state")}
          value={state}
          onChange={(e) => setState(e.target.value)}
        />
        <Input
          placeholder={t("settings.fiscal.zip")}
          value={zip}
          onChange={(e) => setZip(e.target.value)}
        />
      </div>

      <div>
        <Button onClick={save} disabled={update.isPending}>
          {update.isPending ? t("settings.fiscal.saving") : t("settings.fiscal.save")}
        </Button>
      </div>
    </div>
  )
}

// Config → Datos del local: régimen fiscal + la dirección que usa el motor de
// impuestos (TaxJar) para calcular la tasa por zona. Editable por OWNER/MANAGER.
export function FiscalAddressCard() {
  const settings = useFiscalSettings()
  if (settings.isPending) return <Spinner className="size-5 text-muted-foreground" />
  if (!settings.data) return null
  return <AddressForm settings={settings.data} />
}
