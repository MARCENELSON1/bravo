import type { ReactNode } from "react"

import { WellnodMark } from "@/components/brand/wellnod-mark"

// Split-screen shell reused by every identity screen. Minimal centered form on
// the left, brand image on the right (hidden on mobile). Changing this re-skins
// all auth pages.
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
    <div className="grid min-h-svh lg:grid-cols-2">
      <main className="flex min-h-svh flex-col bg-background px-6 py-8">
        {/* Marca arriba, centrada */}
        <div className="flex items-center justify-center gap-2 py-4">
          <WellnodMark className="h-8 w-auto text-primary" />
          <span className="font-heading text-lg tracking-tight">
            <span className="font-bold text-foreground">Well</span>
            <span className="font-light text-foreground/55">nod</span>
          </span>
        </div>

        {/* Contenido centrado */}
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">
            <div className="mb-6 flex flex-col items-center gap-2 text-center">
              <h1 className="font-heading text-3xl font-bold tracking-tight text-foreground">
                {title}
              </h1>
              {description ? (
                <p className="text-sm text-muted-foreground">{description}</p>
              ) : null}
            </div>
            {children}
            {footer ? (
              <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>
            ) : null}
          </div>
        </div>

        {/* Links de pie */}
        <div className="flex items-center justify-center gap-3 py-2 text-xs text-muted-foreground">
          <a href="#" className="transition-colors hover:text-foreground">
            Ayuda
          </a>
          <span aria-hidden>/</span>
          <a href="#" className="transition-colors hover:text-foreground">
            Términos
          </a>
          <span aria-hidden>/</span>
          <a href="#" className="transition-colors hover:text-foreground">
            Privacidad
          </a>
        </div>
      </main>

      {/* Panel de imagen (oculto en mobile) */}
      <aside
        aria-hidden
        className="relative hidden bg-cover bg-center lg:block"
        style={{ backgroundImage: "url('/app-bg.png')" }}
      >
        <div className="absolute inset-0 bg-primary/10" />
      </aside>
    </div>
  )
}
