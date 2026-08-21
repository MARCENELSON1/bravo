import { Moon, Sun } from "lucide-react"

import { useTheme } from "@/presentation/hooks/use-theme"
import { cn } from "@/presentation/lib/cn"

/**
 * El ícono lo elige CSS (`dark:`), no el estado de React.
 *
 * La página se prerenderiza en el build: si el ícono dependiera del estado, el
 * servidor dibujaría la luna (no hay `document`, asume claro) y el cliente el
 * sol (el script inline de index.html ya aplicó la clase `dark`) → mismatch de
 * hidratación. Con clases, el markup es idéntico en los dos lados y el tema se
 * resuelve al pintar. Por lo mismo el aria-label es estable.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { toggle } = useTheme()
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Cambiar tema"
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-xl border border-border text-muted-foreground transition duration-200 ease-out hover:bg-accent hover:text-accent-foreground active:scale-[0.97]",
        className,
      )}
    >
      <Sun className="hidden size-[18px] dark:block" />
      <Moon className="size-[18px] dark:hidden" />
    </button>
  )
}
