import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { FiscalSettingsDTO } from "@/api/types-tenant"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useFiscalSettings, useUpdateFiscalAddress } from "@/hooks/use-tenant"

const REGIME_LABEL: Record<string, string> = {
  AR_AFIP: "Argentina · AFIP (IVA incluido)",
  US_SALES_TAX: "EE.UU. · Sales tax",
}
const ENGINE_LABEL: Record<string, string> = {
  NONE: "Nativo (sin motor externo)",
  TAXJAR: "TaxJar",
  AVALARA: "Avalara",
}

// The form owns its state, seeded once from the loaded settings (no effect sync).
function AddressForm({ settings }: { settings: FiscalSettingsDTO }) {
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
        onSuccess: () => toast.success("Dirección fiscal guardada."),
        onError: (e) =>
          toast.error(isApiError(e) ? e.message : "No pudimos guardar la dirección."),
      }
    )
  }

  return (
    <div className="flex flex-col gap-4 py-4">
      <div>
        <p className="text-sm font-medium text-foreground">Dirección fiscal del local</p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {usesAddress
            ? "El motor de impuestos la usa para calcular la tasa por zona."
            : "Tu régimen no la usa para impuestos (el IVA ya va en el precio); igual podés guardarla como dato del local."}
        </p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            {REGIME_LABEL[settings.tax_regime] ?? settings.tax_regime}
          </span>
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            Impuestos: {ENGINE_LABEL[settings.tax_engine] ?? settings.tax_engine}
          </span>
          <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
            {settings.currency}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Input
          placeholder="Calle y número"
          value={street}
          onChange={(e) => setStreet(e.target.value)}
        />
        <Input placeholder="Ciudad" value={city} onChange={(e) => setCity(e.target.value)} />
        <Input
          placeholder="Estado / provincia"
          value={state}
          onChange={(e) => setState(e.target.value)}
        />
        <Input
          placeholder="Código postal (ZIP)"
          value={zip}
          onChange={(e) => setZip(e.target.value)}
        />
      </div>

      <div>
        <Button onClick={save} disabled={update.isPending}>
          {update.isPending ? "Guardando…" : "Guardar dirección"}
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
