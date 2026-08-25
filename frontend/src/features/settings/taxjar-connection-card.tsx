import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
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
  const connect = useConnectTaxJar()
  const disconnect = useDisconnectTaxJar()
  const [token, setToken] = useState("")
  const [useSandbox, setUseSandbox] = useState(sandbox ?? true)

  const save = () => {
    if (!token.trim()) {
      toast.error("Pegá el API token de TaxJar.")
      return
    }
    connect.mutate(
      { api_token: token.trim(), sandbox: useSandbox },
      {
        onSuccess: () => {
          setToken("")
          toast.success("TaxJar conectado.")
        },
        onError: (e) =>
          toast.error(isApiError(e) ? e.message : "No pudimos conectar TaxJar."),
      }
    )
  }

  const remove = () => {
    disconnect.mutate(undefined, {
      onSuccess: () => toast.success("TaxJar desconectado."),
      onError: (e) =>
        toast.error(isApiError(e) ? e.message : "No pudimos desconectar TaxJar."),
    })
  }

  return (
    <div className="flex flex-col gap-4 py-4">
      <div>
        <p className="text-sm font-medium text-foreground">Reportar impuestos a TaxJar</p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Conectá la cuenta de TaxJar de tu local para que presente y remita las
          declaraciones de sales tax (AutoFile). El reporte se hace bajo tu propia cuenta.
        </p>
        {!connected ? (
          <p className="mt-1 text-xs text-muted-foreground">
            ¿No tenés el token? Lo generás en{" "}
            <a
              href="https://app.taxjar.com/account#api-access"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-foreground underline underline-offset-2"
            >
              TaxJar → Account → API access
            </a>
            . Verificamos el token al conectar.
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
            {connected ? "Conectado" : "No conectado"}
          </span>
          {connected ? (
            <span className="rounded-full border border-border px-2 py-0.5 text-muted-foreground">
              {sandbox ? "Sandbox (pruebas)" : "Producción"}
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <Input
          type="password"
          placeholder={connected ? "Pegá un token nuevo para reemplazar" : "API token de TaxJar"}
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
          Usar entorno de pruebas (sandbox). Desmarcá para producción.
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={save} disabled={connect.isPending}>
          {connect.isPending ? "Conectando…" : connected ? "Actualizar token" : "Conectar TaxJar"}
        </Button>
        {connected ? (
          <Button variant="outline" onClick={remove} disabled={disconnect.isPending}>
            {disconnect.isPending ? "Desconectando…" : "Desconectar"}
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
