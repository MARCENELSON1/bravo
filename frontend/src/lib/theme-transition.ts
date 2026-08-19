import { flushSync } from "react-dom"

type ViewTransitionDocument = Document & {
  startViewTransition?: (callback: () => void) => { ready: Promise<void> }
}

// Cambia el tema con el cross-fade de la View Transitions API. Cae a switch
// instantáneo si no hay soporte o si hay reduce-motion (OS o preferencia de la app).
export function setThemeAnimated(setTheme: (theme: string) => void, value: string) {
  const doc = document as ViewTransitionDocument
  const reduceMotion =
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    document.documentElement.classList.contains("reduce-motion")

  if (!doc.startViewTransition || reduceMotion) {
    setTheme(value)
    return
  }
  doc.startViewTransition(() => {
    flushSync(() => setTheme(value))
  })
}
