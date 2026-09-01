import { useEffect, useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { FiscalCondition } from "@/api/types-invoicing"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import {
  useAfipConnection,
  useConnectAfip,
  useDisconnectAfip,
  useDisconnectMp,
  useMpConnection,
} from "@/hooks/use-integrations"
import { FISCAL_CONDITION_LABELS } from "@/lib/invoice-labels"
import { useServices } from "@/services/services-context"

// Route standalone: /app/integrations. También es el destino del callback OAuth de
// MercadoPago (?mp=ok|error). El contenido vive en <IntegrationsPanel/> para poder
// reutilizarlo dentro de la sección "Integraciones" de Configuración.
export function IntegrationsPage() {
  const { t } = useTranslation()
  const [params, setParams] = useSearchParams()

  // The OAuth callback redirects back here with ?mp=ok|error.
  useEffect(() => {
    const result = params.get("mp")
    if (!result) return
    if (result === "ok") toast.success(t("integrations.mpConnectedToast"))
    else toast.error(t("integrations.mpConnectError"))
    setParams({}, { replace: true })
  }, [params, setParams, t])

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {t("integrations.title")}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">{t("integrations.subtitle")}</p>
      </header>

      <IntegrationsPanel />
    </div>
  )
}

// Bloque embebido para Configuración: título + descripción + contenido, con el
// mismo ritmo vertical (py-5) que las filas del resto de las secciones.
function Section({
  title,
  desc,
  children,
}: {
  title: string
  desc?: string
  children: ReactNode
}) {
  return (
    <div className="py-5">
      <p className="text-sm font-medium text-foreground">{title}</p>
      {desc ? <p className="mt-0.5 text-sm text-muted-foreground">{desc}</p> : null}
      <div className="mt-3 flex flex-col gap-3">{children}</div>
    </div>
  )
}

export function IntegrationsPanel({ embedded = false }: { embedded?: boolean }) {
  const { t } = useTranslation()
  const connection = useMpConnection()
  const disconnect = useDisconnectMp()
  const { integrationsApi } = useServices()

  const connect = async () => {
    try {
      const { url } = await integrationsApi.getMpConnectUrl()
      window.location.href = url
    } catch (error) {
      toast.error(apiErrorText(error, t, t("integrations.mp.startError")))
    }
  }

  const data = connection.data

  const mpContent = (
    <>
      {connection.isPending ? (
        <Spinner className="size-5 text-muted-foreground" />
      ) : data?.connected ? (
        <>
          <div className="flex items-center gap-2 text-sm">
            <span className="size-2 rounded-full bg-success" />
            <span>
              {t("integrations.mp.connected")}
              {data.nickname ? ` · ${data.nickname}` : ""}
              {!data.live_mode ? t("integrations.mp.sandboxSuffix") : ""}
            </span>
          </div>
          <Button
            variant="outline"
            disabled={disconnect.isPending}
            onClick={() =>
              disconnect.mutate(undefined, {
                onSuccess: () => toast.success(t("integrations.mp.disconnectedToast")),
                onError: (error) =>
                  toast.error(apiErrorText(error, t, t("integrations.mp.disconnectError"))),
              })
            }
          >
            {disconnect.isPending
              ? t("integrations.mp.disconnecting")
              : t("integrations.mp.disconnect")}
          </Button>
        </>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{t("integrations.mp.notConnected")}</p>
          <Button onClick={connect}>{t("integrations.mp.connect")}</Button>
        </>
      )}
    </>
  )

  // Modo embebido: secciones separadas por dividers, sin Card propio, para vivir
  // dentro de un GlassCard de Configuración con la misma estética que el resto.
  if (embedded) {
    return (
      <div className="divide-y divide-border">
        <Section title={t("integrations.mp.title")} desc={t("integrations.mp.description")}>
          {mpContent}
        </Section>
        <AfipCard embedded />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>{t("integrations.mp.title")}</CardTitle>
          <CardDescription>{t("integrations.mp.description")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">{mpContent}</CardContent>
      </Card>

      <AfipCard />
    </div>
  )
}

const FISCAL_CONDITIONS: { value: FiscalCondition; label: string }[] = [
  { value: "RESPONSABLE_INSCRIPTO", label: FISCAL_CONDITION_LABELS.RESPONSABLE_INSCRIPTO },
  { value: "MONOTRIBUTO", label: FISCAL_CONDITION_LABELS.MONOTRIBUTO },
]

// ARCA (facturación electrónica): the tenant pastes its certificate + private key
// and CUIT. Credentials are sent once and stored encrypted server-side; the UI
// never reads them back.
function AfipCard({ embedded = false }: { embedded?: boolean }) {
  const { t } = useTranslation()
  const connection = useAfipConnection()
  const connect = useConnectAfip()
  const disconnect = useDisconnectAfip()
  const [cuit, setCuit] = useState("")
  const [pointOfSale, setPointOfSale] = useState("1")
  const [fiscalCondition, setFiscalCondition] = useState<FiscalCondition>("RESPONSABLE_INSCRIPTO")
  const [certificate, setCertificate] = useState("")
  const [privateKey, setPrivateKey] = useState("")

  const data = connection.data

  const submit = () => {
    const pos = Number(pointOfSale)
    if (!/^\d{11}$/.test(cuit.trim())) {
      toast.error(t("integrations.afip.invalidCuit"))
      return
    }
    if (!Number.isInteger(pos) || pos < 1) {
      toast.error(t("integrations.afip.invalidPos"))
      return
    }
    if (!certificate.includes("BEGIN CERTIFICATE") || !privateKey.includes("PRIVATE KEY")) {
      toast.error(t("integrations.afip.invalidPem"))
      return
    }
    connect.mutate(
      {
        cuit: cuit.trim(),
        certificate: certificate.trim(),
        private_key: privateKey.trim(),
        point_of_sale: pos,
        fiscal_condition: fiscalCondition,
      },
      {
        onSuccess: () => {
          toast.success(t("integrations.afip.connectedToast"))
          setCertificate("")
          setPrivateKey("")
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("integrations.afip.connectError"))),
      }
    )
  }

  const content = (
    <>
      {connection.isPending ? (
        <Spinner className="size-5 text-muted-foreground" />
      ) : data?.connected ? (
        <>
          <div className="flex items-center gap-2 text-sm">
            <span className="size-2 rounded-full bg-success" />
            <span>
              {t("integrations.afip.connected", {
                cuit: data.cuit,
                pos: data.point_of_sale,
              })}
              {!data.live_mode ? t("integrations.afip.homologationSuffix") : ""}
            </span>
          </div>
          <Button
            variant="outline"
            disabled={disconnect.isPending}
            onClick={() =>
              disconnect.mutate(undefined, {
                onSuccess: () => toast.success(t("integrations.afip.disconnectedToast")),
                onError: (error) =>
                  toast.error(apiErrorText(error, t, t("integrations.afip.disconnectError"))),
              })
            }
          >
            {disconnect.isPending
              ? t("integrations.afip.disconnecting")
              : t("integrations.afip.disconnect")}
          </Button>
        </>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <Label htmlFor="afip-cuit">{t("integrations.afip.cuitLabel")}</Label>
              <Input
                id="afip-cuit"
                inputMode="numeric"
                placeholder="20111111112"
                value={cuit}
                onChange={(e) => setCuit(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="afip-pos">{t("integrations.afip.posLabel")}</Label>
              <Input
                id="afip-pos"
                type="number"
                min={1}
                value={pointOfSale}
                onChange={(e) => setPointOfSale(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <Label>{t("integrations.afip.fiscalConditionLabel")}</Label>
            <Select
              value={fiscalCondition}
              onValueChange={(v) => setFiscalCondition(v as FiscalCondition)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FISCAL_CONDITIONS.map((f) => (
                  <SelectItem key={f.value} value={f.value}>
                    {f.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="afip-cert">{t("integrations.afip.certificateLabel")}</Label>
            <Textarea
              id="afip-cert"
              placeholder="-----BEGIN CERTIFICATE-----"
              value={certificate}
              onChange={(e) => setCertificate(e.target.value)}
              className="font-mono text-xs"
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="afip-key">{t("integrations.afip.privateKeyLabel")}</Label>
            <Textarea
              id="afip-key"
              placeholder="-----BEGIN PRIVATE KEY-----"
              value={privateKey}
              onChange={(e) => setPrivateKey(e.target.value)}
              className="font-mono text-xs"
            />
          </div>
          <Button onClick={submit} disabled={connect.isPending}>
            {connect.isPending
              ? t("integrations.afip.connecting")
              : t("integrations.afip.connect")}
          </Button>
        </>
      )}
    </>
  )

  if (embedded) {
    return (
      <Section title={t("integrations.afip.title")} desc={t("integrations.afip.description")}>
        {content}
      </Section>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("integrations.afip.title")}</CardTitle>
        <CardDescription>{t("integrations.afip.description")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">{content}</CardContent>
    </Card>
  )
}
