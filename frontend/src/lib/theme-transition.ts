import { flushSync } from "react-dom"

type ViewTransitionDocument = Document & {
  startViewTransition?: (callback: () => void) => { ready: Promise<void> }
}

// Cambia el tema con el cross-fade de la View Transitions API. Cae a switch
// instantáneo si no hay soporte, si está activo "Reducir movimiento" de la app, o
// en móvil: ahí la View Transitions API bugea el backdrop-filter (el "liquid glass")
// y el fondo `fixed`, así que en pantallas chicas cambiamos el tema al instante.
export function setThemeAnimated(setTheme: (theme: string) => void, value: string) {
  const doc = document as ViewTransitionDocument
  const reduceMotion = document.documentElement.classList.contains("reduce-motion")
  const isMobile =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 767px)").matches

  if (!doc.startViewTransition || reduceMotion || isMobile) {
    setTheme(value)
    return
  }
  doc.startViewTransition(() => {
    flushSync(() => setTheme(value))
  })
}
