import { useEffect, useState } from "react"
import { QRCodeSVG } from "qrcode.react"
import { useSearchParams } from "react-router-dom"

import { usePresenceChallenge } from "@/hooks/use-timeclock"
import { readStoredDeviceToken, secondsUntil, storeDeviceToken } from "@/lib/presence"

// Local display screen: shows a rotating QR + short code that employees scan or
// type from their own phone to fichar. Public route (no employee session) —
// authenticated as a device via a token the OWNER provisions (URL `?device=`).
// Responsive: fills the screen on a mounted monitor and on a phone/tablet alike.
export function PresenceDisplayPage() {
  const [params] = useSearchParams()
  const fromUrl = params.get("device")
  // Derive the token (URL on first open, else the persisted one) — no effect
  // state churn. The effect only persists it for subsequent visits.
  const deviceToken = fromUrl ?? readStoredDeviceToken()
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (fromUrl) storeDeviceToken(fromUrl)
  }, [fromUrl])

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const challenge = usePresenceChallenge(deviceToken)

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-8 bg-background px-6 py-10 text-center">
      <div className="flex flex-col gap-1">
        <span className="font-heading text-2xl font-semibold sm:text-3xl">Fichaje</span>
        <span className="text-sm text-muted-foreground">
          Escaneá el QR o ingresá el código desde tu celular.
        </span>
      </div>

      {!deviceToken ? (
        <p className="max-w-sm text-balance text-muted-foreground">
          Este dispositivo no está configurado. Pedile al dueño el enlace de fichaje
          (Personal → Dispositivo de fichaje) y abrilo en esta pantalla.
        </p>
      ) : challenge.isError ? (
        <p className="max-w-sm text-balance text-destructive">
          No pudimos validar este dispositivo. Volvé a abrir el enlace de fichaje.
        </p>
      ) : challenge.data ? (
        <>
          <div className="rounded-2xl bg-white p-6 shadow-sm sm:p-8">
            <QRCodeSVG
              value={challenge.data.qr_payload}
              marginSize={2}
              className="h-56 w-56 sm:h-72 sm:w-72"
            />
          </div>
          <div className="flex flex-col items-center gap-1">
            <span className="text-xs uppercase tracking-wider text-muted-foreground">Código</span>
            <span className="font-mono text-4xl font-bold tracking-[0.3em] sm:text-5xl">
              {challenge.data.code}
            </span>
            <span className="text-xs text-muted-foreground">
              Cambia en {secondsUntil(challenge.data.expires_at, now)} s
            </span>
          </div>
        </>
      ) : (
        <div className="h-72 w-72 animate-pulse rounded-2xl bg-muted" />
      )}
    </div>
  )
}
