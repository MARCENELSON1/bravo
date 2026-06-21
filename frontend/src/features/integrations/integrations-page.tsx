import { useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useDisconnectMp, useMpConnection } from "@/hooks/use-integrations"
import { useServices } from "@/services/services-context"

export function IntegrationsPage() {
  const connection = useMpConnection()
  const disconnect = useDisconnectMp()
  const { integrationsApi } = useServices()
  const [params, setParams] = useSearchParams()

  // The OAuth callback redirects back here with ?mp=ok|error.
  useEffect(() => {
    const result = params.get("mp")
    if (!result) return
    if (result === "ok") toast.success("MercadoPago conectado.")
    else toast.error("No pudimos conectar MercadoPago. Probá de nuevo.")
    setParams({}, { replace: true })
  }, [params, setParams])

  const connect = async () => {
    try {
      const { url } = await integrationsApi.getMpConnectUrl()
      window.location.href = url
    } catch (error) {
      toast.error(isApiError(error) ? error.message : "No pudimos iniciar la conexión.")
    }
  }

  const data = connection.data

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Integraciones
        </GradientHeading>
        <p className="text-sm text-muted-foreground">Conectá tus medios de cobro.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>MercadoPago</CardTitle>
          <CardDescription>
            Conectá la cuenta de tu local. Los cobros por MercadoPago/QR caen directo a tu cuenta.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {connection.isPending ? (
            <Spinner className="size-5 text-muted-foreground" />
          ) : data?.connected ? (
            <>
              <div className="flex items-center gap-2 text-sm">
                <span className="size-2 rounded-full bg-emerald-500" />
                <span>
                  Conectado
                  {data.nickname ? ` · ${data.nickname}` : ""}
                  {!data.live_mode ? " · sandbox" : ""}
                </span>
              </div>
              <Button
                variant="outline"
                disabled={disconnect.isPending}
                onClick={() =>
                  disconnect.mutate(undefined, {
                    onSuccess: () => toast.success("MercadoPago desconectado."),
                    onError: (error) =>
                      toast.error(
                        isApiError(error) ? error.message : "No pudimos desconectar."
                      ),
                  })
                }
              >
                {disconnect.isPending ? "Desconectando…" : "Desconectar"}
              </Button>
            </>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">No conectado.</p>
              <Button onClick={connect}>Conectar con MercadoPago</Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
