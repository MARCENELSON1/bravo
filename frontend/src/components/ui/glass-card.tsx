import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

// Frosted-glass card (identidad Wellnod): variante clara y oscura. El fondo
// escénico del shell se trasluce detrás; agregá el padding con className.
export function GlassCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-black/10 bg-white/55 shadow-xl shadow-black/5 backdrop-blur-2xl dark:border-white/10 dark:bg-white/[0.045] dark:shadow-black/20",
        className
      )}
      {...props}
    />
  )
}
