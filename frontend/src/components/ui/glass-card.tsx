import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

// Superficie de vidrio de Wellnod. Única fuente: la usan tanto las tarjetas
// (GlassCard) como los paneles del shell —sidebar y área principal—, para que no
// haya dos vidrios distintos conviviendo.
export const GLASS_SURFACE =
  "rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl " +
  "dark:border-white/10 dark:bg-black/30"

// Y el mismo vidrio, teñido del verde de la marca. Lo lleva la tarjeta que trae una
// buena noticia —ganancia en positivo, caja abierta, cobros del día— y ninguna otra:
// si lo llevaran todas, el color no diría nada.
//
// El fondo lo pone `.glass-positive` (ver index.css), que está fuera de @layer y por
// eso le gana al `bg-` de arriba sin tener que quitárselo. El borde va acá porque
// entre dos utilidades de Tailwind gana la última, que es lo que hace `cn`.
const GLASS_POSITIVE = "glass-positive border-primary/25 dark:border-primary/30"

/** El vidrio de la tarjeta: el neutro de siempre, o el verde de una buena noticia. */
export type GlassTone = "neutral" | "positive"

// Tarjeta de vidrio. Suma sombra a la superficie: flota sobre el fondo escénico,
// a diferencia de los paneles del shell, que son el marco. El padding va por
// className.
export function GlassCard({
  className,
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLDivElement> & { tone?: GlassTone }) {
  return (
    <div
      className={cn(
        GLASS_SURFACE,
        tone === "positive" && GLASS_POSITIVE,
        "shadow-xl shadow-black/5 dark:shadow-black/20",
        className
      )}
      {...props}
    />
  )
}
