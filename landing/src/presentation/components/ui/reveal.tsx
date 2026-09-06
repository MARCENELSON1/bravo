import type { CSSProperties, ElementType, ReactNode } from "react"

import { useReveal } from "@/presentation/hooks/use-reveal"
import { cn } from "@/presentation/lib/cn"

type Anim = "rise" | "fade" | "scale" | "lift" | "left"

// Revela contenido al entrar en viewport. `anim` elige el gesto y `delay` lo
// retrasa; el movimiento real vive en el CSS (.reveal), que respeta "reducir
// movimiento". `as` permite que el envoltorio sea el elemento semántico correcto
// —una <li>, una <section>— en vez de forzar un <div> de más.
export function Reveal({
  children,
  className,
  style,
  anim = "rise",
  delay = 0,
  as: Tag = "div",
}: {
  children: ReactNode
  className?: string
  style?: CSSProperties
  anim?: Anim
  /** Milisegundos de espera antes de arrancar. */
  delay?: number
  as?: ElementType
}) {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <Tag
      ref={ref}
      data-anim={anim}
      className={cn("reveal", visible && "is-visible", className)}
      style={delay ? { ...style, "--reveal-delay": `${delay}ms` } as CSSProperties : style}
    >
      {children}
    </Tag>
  )
}

// Igual que Reveal, pero escalona a sus hijos directos: el primero entra, el
// segundo 70 ms después, y así. Evita repartir delays a mano por el JSX.
export function Stagger({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode
  className?: string
  as?: ElementType
}) {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <Tag ref={ref} className={cn("stagger", visible && "is-visible", className)}>
      {children}
    </Tag>
  )
}
