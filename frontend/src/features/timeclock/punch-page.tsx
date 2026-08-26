import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { usePresencePunch } from "@/hooks/use-timeclock"
import { isScannerSupported } from "@/lib/presence"

// Employee fichaje by presence: type the rotating code shown on the local
// display, or scan its QR with the camera. Either way the punch belongs to the
// logged-in user (source=PRESENCE). The topbar toggle stays as the quick path.
export function PunchPage() {
  const { t } = useTranslation()
  const punch = usePresencePunch()
  const [code, setCode] = useState("")
  const [scanning, setScanning] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const doPunch = (presented: string) => {
    const value = presented.trim()
    if (!value) {
      toast.error(t("timeclock.punch.emptyCode"))
      return
    }
    punch.mutate(value, {
      onSuccess: (shift) => {
        toast.success(
          shift.status === "OPEN"
            ? t("timeclock.punch.clockedIn")
            : t("timeclock.punch.clockedOut")
        )
        setCode("")
      },
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("timeclock.punch.punchError"))),
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
        toast.error(t("timeclock.punch.cameraError"))
        setScanning(false)
      }
    }

    void start()
    return () => {
      stopped = true
      if (timer) clearInterval(timer)
      if (stream) stream.getTracks().forEach((track) => track.stop())
    }
  }, [scanning, t])

  return (
    <div className="mx-auto flex max-w-sm flex-col gap-6 px-6 py-10">
      <div className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {t("timeclock.punch.title")}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          {t("timeclock.punch.subtitle")}
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <Input
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder={t("timeclock.punch.codePlaceholder")}
          autoCapitalize="characters"
          autoComplete="off"
          className="text-center font-mono text-lg tracking-[0.3em]"
        />
        <Button onClick={() => doPunch(code)} disabled={punch.isPending}>
          {punch.isPending ? t("timeclock.punch.submitting") : t("timeclock.punch.submit")}
        </Button>

        {isScannerSupported() ? (
          <Button variant="outline" onClick={() => setScanning((s) => !s)}>
            {scanning ? t("timeclock.punch.stopScan") : t("timeclock.punch.scan")}
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
