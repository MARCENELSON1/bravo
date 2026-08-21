import { useCallback, useEffect, useState } from "react"

type Theme = "light" | "dark"
const STORAGE_KEY = "wellnod-landing:theme"

function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light"
}

// Controla el tema claro/oscuro togglear la clase .dark en <html> y persistir la
// preferencia. El flash inicial ya lo evita el script inline de index.html.
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() =>
    typeof document === "undefined" ? "light" : currentTheme(),
  )

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
