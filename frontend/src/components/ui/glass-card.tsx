import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

// Superficie de vidrio de Wellnod. Única fuente: la usan tanto las tarjetas
// (GlassCard) como los paneles del shell —sidebar y área principal—, para que no
// haya dos vidrios distintos conviviendo.
export const GLASS_SURFACE =
  "rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl " +
  "dark:border-white/10 dark:bg-black/30"

// Tarjeta de vidrio. Suma sombra a la superficie: flota sobre el fondo escénico,
// a diferencia de los paneles del shell, que son el marco. El padding va por
// className.
export function GlassCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        GLASS_SURFACE,
        "shadow-xl shadow-black/5 dark:shadow-black/20",
        className
      )}
      {...props}
    />
  )
}
