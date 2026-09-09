import type { ReactNode } from "react"

import { GradientHeading } from "@/components/ui/gradient-heading"

// El contenido de la tarjeta en las pantallas de identidad: encabezado, formulario
// y pie. Nada más.
//
// El marco —fondo, relato de marca y la tarjeta de vidrio— lo pone <AuthShell />,
// que es un layout route y por eso no se desmonta al cambiar de pantalla. Que esto
// sea solo el contenido es lo que hace que pasar de iniciar sesión a crear comercio
// no parpadee: el vidrio se queda y adentro se cruzan los textos.
export function AuthLayout({
  title,
  description,
  children,
  footer,
}: {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <>
      {/* El margen de abajo se aprieta en la variante ancha (ver .auth-head). */}
      <div className="auth-head flex flex-col gap-1">
        <GradientHeading size="sm" weight="bold">
          {title}
        </GradientHeading>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {children}
      {/* El pie va al fondo de la tarjeta, no pegado al formulario: ver .auth-foot. */}
      {footer ? (
        <div className="auth-foot text-center text-sm text-muted-foreground">{footer}</div>
      ) : null}
    </>
  )
}
