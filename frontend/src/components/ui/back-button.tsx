import { Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"

import { cn } from "@/lib/utils"

// El control de "volver", uno solo para toda la app. Nació en Configuración y
// ahora vive acá: cada pantalla que lo copiaba a mano terminaba con su propia
// versión —una flecha suelta, un link subrayado, un cuadradito con borde— y
// volver atrás se veía distinto según dónde estuvieras.
//
// Es texto con flecha, sin fondo ni borde: es una salida, no una acción de la
// pantalla, y no tiene que competir con el botón principal.
//
// Navega (`to`) o ejecuta (`onClick`), nunca las dos: el tipo lo obliga.
type BackButtonProps = { label: string; className?: string } & (
  | { to: string; onClick?: never }
  | { onClick: () => void; to?: never }
)

export function BackButton({ label, className, to, onClick }: BackButtonProps) {
  const classes = cn(
    "inline-flex shrink-0 items-center gap-1.5 self-start rounded-lg text-sm font-medium",
    "text-muted-foreground transition duration-200 ease-out hover:text-foreground",
    "focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none",
    "active:scale-[0.97]",
    className
  )

  const content = (
    <>
      <ArrowLeft className="size-4" />
      {label}
    </>
  )

  return to ? (
    <Link to={to} className={classes}>
      {content}
    </Link>
  ) : (
    <button type="button" onClick={onClick} className={classes}>
      {content}
    </button>
  )
}
