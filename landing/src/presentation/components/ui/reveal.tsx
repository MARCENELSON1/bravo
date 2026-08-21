import type { ReactNode } from "react"

import { useReveal } from "@/presentation/hooks/use-reveal"
import { cn } from "@/presentation/lib/cn"

// Envuelve contenido para que aparezca con un fade suave al entrar en viewport.
export function Reveal({
  children,
  className,
  style,
}: {
  children: ReactNode
  className?: string
  style?: React.CSSProperties
}) {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <div ref={ref} className={cn("reveal", visible && "is-visible", className)} style={style}>
      {children}
    </div>
  )
}
