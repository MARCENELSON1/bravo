import { Moon, Sun } from "lucide-react"

import { useTheme } from "@/presentation/hooks/use-theme"
import { cn } from "@/presentation/lib/cn"

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme()
  const isDark = theme === "dark"
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-xl border border-border text-muted-foreground transition duration-200 ease-out hover:bg-accent hover:text-accent-foreground active:scale-[0.97]",
        className,
      )}
    >
      {isDark ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
    </button>
  )
}
