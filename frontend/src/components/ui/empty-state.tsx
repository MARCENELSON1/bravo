import type { ReactNode } from "react"
import { Inbox } from "lucide-react"

import { cn } from "@/lib/utils"

// Estado vacío de una tabla o lista. Antes esto era un bloque de `p-8` copiado en
// once lugares: alto, sin ícono y con el fondo escrito a mano en gris crudo. Acá
// queda en una sola definición, más compacto (el ícono y el texto van en línea) y
// usando el token `muted` en vez de bg-black/[0.06] + su variante dark.
export function EmptyState({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-center gap-2 bg-muted/30 px-6 py-6 text-center",
        className
      )}
    >
      <Inbox className="size-4 shrink-0 text-muted-foreground/60" aria-hidden />
      <span className="text-sm font-medium text-muted-foreground">{children}</span>
    </div>
  )
}
