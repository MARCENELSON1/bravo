import { useEffect, useState } from "react"

// true en pantallas < sm (640px, el breakpoint de Tailwind). Se actualiza al
// redimensionar/rotar. Sirve para decidir dropdown (desktop) vs modal (mobile).
const QUERY = "(max-width: 639px)"

export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.matchMedia(QUERY).matches
  )
  useEffect(() => {
    const mql = window.matchMedia(QUERY)
    const onChange = () => setIsMobile(mql.matches)
    onChange()
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])
  return isMobile
}
