// Presence-layer helpers (kept out of component files so pages export only
// components — eslint react-refresh rule).

const DEVICE_TOKEN_KEY = "nucleo_presence_device_token"

// The display persists its device token so it survives reloads. The token is
// provisioned once by the OWNER (passed via the URL `?device=<token>`).
export function readStoredDeviceToken(): string | null {
  try {
    return localStorage.getItem(DEVICE_TOKEN_KEY)
  } catch {
    return null
  }
}

export function storeDeviceToken(token: string): void {
  try {
    localStorage.setItem(DEVICE_TOKEN_KEY, token)
  } catch {
    // localStorage unavailable (private mode) — the token stays in memory only.
  }
}

// URL the OWNER opens on the local display screen to bootstrap it.
export function buildDisplayUrl(token: string): string {
  return `${window.location.origin}/fichaje?device=${encodeURIComponent(token)}`
}

export function isScannerSupported(): boolean {
  return typeof window !== "undefined" && "BarcodeDetector" in window
}

// Seconds remaining until an ISO instant (never negative).
export function secondsUntil(iso: string, now: number): number {
  return Math.max(0, Math.round((new Date(iso).getTime() - now) / 1000))
}
