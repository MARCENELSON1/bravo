import type { ReactNode } from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

// Class-strategy theming (matches the `.dark` variant in index.css). Persists the
// choice and respects the OS preference by default.
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  )
}
