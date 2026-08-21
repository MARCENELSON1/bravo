import { useCallback, useEffect, useState } from "react"

type Theme = "light" | "dark"
const STORAGE_KEY = "wellnod-landing:theme"

function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light"
}

// Controla el tema claro/oscuro togglear la clase .dark en <html> y persistir la
// preferencia. El flash inicial ya lo evita el script inline de index.html.
export function useTheme() {
  // Estado inicial determinista: durante el prerender no hay `document`, así que
  // cualquier lectura del DOM haría diferir servidor y cliente. Se sincroniza al
  // montar; quien necesite el tema para pintar debe usar las clases `dark:`.
  const [theme, setThemeState] = useState<Theme>("light")

  useEffect(() => {
    setThemeState(currentTheme())
  }, [])

  const setTheme = useCallback((next: Theme) => {
    document.documentElement.classList.toggle("dark", next === "dark")
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // ignora modo privado / storage no disponible
    }
    setThemeState(next)
  }, [])

  const toggle = useCallback(() => {
    setTheme(currentTheme() === "dark" ? "light" : "dark")
  }, [setTheme])

  // Mantiene el estado en sync si el tema cambia en otra pestaña.
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setThemeState(currentTheme())
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  return { theme, toggle, setTheme }
}
