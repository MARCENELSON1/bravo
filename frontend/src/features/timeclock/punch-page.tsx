import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { usePresencePunch } from "@/hooks/use-timeclock"
import { isScannerSupported } from "@/lib/presence"

// Employee fichaje by presence: type the rotating code shown on the local
// display, or scan its QR with the camera. Either way the punch belongs to the
// logged-in user (source=PRESENCE). The topbar toggle stays as the quick path.
export function PunchPage() {
  const punch = usePresencePunch()
  const [code, setCode] = useState("")
  const [scanning, setScanning] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const doPunch = (presented: string) => {
    const value = presented.trim()
    if (!value) {
      toast.error("Ingresá el código de fichaje.")
      return
    }
    punch.mutate(value, {
      onSuccess: (shift) => {
        toast.success(shift.status === "OPEN" ? "Entrada registrada." : "Salida registrada.")
        setCode("")
      },
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos registrar el fichaje."),
    })
  }
  // Keep a stable ref to the latest handler so the scanner effect depends only
  // on `scanning` (no stale closure, no exhaustive-deps churn).
  const punchRef = useRef(doPunch)
  useEffect(() => {
    punchRef.current = doPunch
  })

  useEffect(() => {
    if (!scanning) return
    let stream: MediaStream | null = null
    let timer: number | undefined
    let stopped = false
    const Detector = window.BarcodeDetector
    const detector = Detector ? new Detector({ formats: ["qr_code"] }) : null

    const start = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        })
        if (stopped) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          await videoRef.current.play()
        }
        timer = window.setInterval(async () => {
          if (!detector || !videoRef.current) return
          try {
            const found = await detector.detect(videoRef.current)
            if (found.length > 0) {
              setScanning(false)
              punchRef.current(found[0].rawValue)
            }
          } catch {
            // frame not decodable yet — keep polling
          }
        }, 400)
      } catch {
        toast.error("No pudimos abrir la cámara. Ingresá el código a mano.")
        setScanning(false)
      }
    }

    void start()
    return () => {
      stopped = true
      if (timer) clearInterval(timer)
      if (stream) stream.getTracks().forEach((t) => t.stop())
    }
  }, [scanning])

  return (
    <div className="mx-auto flex max-w-sm flex-col gap-6 px-6 py-10">
      <div className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Fichar
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          Ingresá el código de la pantalla del local o escaneá el QR.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <Input
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="Código (p. ej. 4F7K2Q)"
          autoCapitalize="characters"
          autoComplete="off"
          className="text-center font-mono text-lg tracking-[0.3em]"
        />
        <Button onClick={() => doPunch(code)} disabled={punch.isPending}>
          {punch.isPending ? "Fichando…" : "Fichar"}
        </Button>

        {isScannerSupported() ? (
          <Button variant="outline" onClick={() => setScanning((s) => !s)}>
            {scanning ? "Detener cámara" : "Escanear con cámara"}
          </Button>
        ) : null}

        {scanning ? (
          <video
            ref={videoRef}
            className="aspect-square w-full rounded-xl bg-black object-cover"
            playsInline
            muted
          />
        ) : null}
      </div>
    </div>
  )
}
