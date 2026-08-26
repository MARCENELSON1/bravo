import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useConnectTaxJar,
  useDisconnectTaxJar,
  useTaxJarConnection,
} from "@/hooks/use-integrations"
import { useFiscalSettings } from "@/hooks/use-tenant"

function ConnectForm({ connected, sandbox }: { connected: boolean; sandbox: boolean | null }) {
  const { t } = useTranslation()
  const connect = useConnectTaxJar()
  const disconnect = useDisconnectTaxJar()
  const [token, setToken] = useState("")
  const [useSandbox, setUseSandbox] = useState(sandbox ?? true)

  const save = () => {
    if (!token.trim()) {
      toast.error(t("settings.taxjar.tokenRequired"))
      return
    }
    connect.mutate(
      { api_token: token.trim(), sandbox: useSandbox },
      {
        onSuccess: () => {
          setToken("")
          toast.success(t("settings.taxjar.connectSuccess"))
        },
        onError: (e) =>
          toast.error(apiErrorText(e, t, t("settings.taxjar.connectError"))),
      }
    )
  }

  const remove = () => {
    disconnect.mutate(undefined, {
      onSuccess: () => toast.success(t("settings.taxjar.disconnectSuccess")),
      onError: (e) =>
        toast.error(apiErrorText(e, t, t("settings.taxjar.disconnectError"))),
    })
  }

  return (
    <div className="flex flex-col gap-4 py-4">
      <div>
        <p className="text-sm font-medium text-foreground">{t("settings.taxjar.title")}</p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {t("settings.taxjar.desc")}
        </p>
        {!connected ? (
          <p className="mt-1 text-xs text-muted-foreground">
            {t("settings.taxjar.hintPre")}{" "}
            <a
              href="https://app.taxjar.com/account#api-access"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-foreground underline underline-offset-2"
            >
              {t("settings.taxjar.hintLink")}
            </a>
            {t("settings.taxjar.hintPost")}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span
            className={
              connected
                ? "rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-emerald-600 dark:text-emerald-400"
                : "rounded-full border border-border px-2 py-0.5 text-muted-foreground"
            }
          >
            {connected ? t("settings.taxjar.connected") : t("settings.taxjar.notConnected")}
          </span>
          {connected ? (
            <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
              {sandbox ? t("settings.taxjar.sandbox") : t("settings.taxjar.production")}
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <Input
          type="password"
          placeholder={
            connected
              ? t("settings.taxjar.tokenPlaceholderReplace")
              : t("settings.taxjar.tokenPlaceholder")
          }
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoComplete="off"
        />
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={useSandbox}
            onChange={(e) => setUseSandbox(e.target.checked)}
            className="size-4 rounded border-border"
          />
          {t("settings.taxjar.sandboxToggle")}
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={save} disabled={connect.isPending}>
          {connect.isPending
            ? t("settings.taxjar.connecting")
            : connected
              ? t("settings.taxjar.updateToken")
              : t("settings.taxjar.connect")}
        </Button>
        {connected ? (
          <Button variant="outline" onClick={remove} disabled={disconnect.isPending}>
            {disconnect.isPending ? t("settings.taxjar.disconnecting") : t("settings.taxjar.disconnect")}
          </Button>
        ) : null}
      </div>
    </div>
  )
}

// Config → Datos del local: conexión de la cuenta de TaxJar del local (reporte
// AutoFile). Solo aparece para locales US/TaxJar; en AR no se muestra (paridad).
export function TaxJarConnectionCard() {
  const fiscal = useFiscalSettings()
  const isTaxJar = fiscal.data?.tax_engine === "TAXJAR"
  const conn = useTaxJarConnection(isTaxJar)
  if (fiscal.data && !isTaxJar) return null // AR / motor nativo: no se muestra
  if (fiscal.isPending || conn.isPending) {
    return <Spinner className="size-5 text-muted-foreground" />
  }
  if (!conn.data) return null
  return <ConnectForm connected={conn.data.connected} sandbox={conn.data.sandbox} />
}
