import { useEffect, useState } from "react"

// Preferencia local "reducir movimiento": apaga animaciones CSS (vía la clase
// .reduce-motion en <html>) y, con el hook, también las de framer-motion.
const KEY = "wellnod:reduce-motion"
const EVENT = "wellnod:reduce-motion"

export function getReduceMotion(): boolean {
  try {
    return localStorage.getItem(KEY) === "1"
  } catch {
    return false
  }
}

export function setReduceMotion(value: boolean) {
  try {
    localStorage.setItem(KEY, value ? "1" : "0")
  } catch {
    /* ignore */
  }
  document.documentElement.classList.toggle("reduce-motion", value)
  window.dispatchEvent(new Event(EVENT))
}

export function useReduceMotion(): boolean {
  const [value, setValue] = useState(getReduceMotion)
  useEffect(() => {
    const update = () => setValue(getReduceMotion())
    window.addEventListener(EVENT, update)
    window.addEventListener("storage", update)
    return () => {
      window.removeEventListener(EVENT, update)
      window.removeEventListener("storage", update)
    }
  }, [])
  return value
}
