import type { ReactNode } from "react"

import { WellnodMark } from "@/components/brand/wellnod-mark"
import { GradientHeading } from "@/components/ui/gradient-heading"

// Split-screen shell reused by every identity screen. The brand panel is hidden
// on mobile; the form sits on the right. Changing this re-skins all auth pages.
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
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-primary to-primary/80 p-10 text-primary-foreground lg:flex">
        {/* soft decorative glow */}
        <div className="pointer-events-none absolute -right-24 -top-24 size-72 rounded-full bg-primary-foreground/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 size-80 rounded-full bg-primary-foreground/5 blur-3xl" />

        <div className="relative flex items-center gap-2">
          <WellnodMark className="h-8 w-auto text-primary-foreground/90" />
          <span className="font-heading text-lg tracking-tight">
            <span className="font-bold">Well</span>
            <span className="font-light text-primary-foreground/70">nod</span>
          </span>
        </div>

        <div className="relative">
          <h2 className="font-heading text-4xl font-semibold leading-tight">
            El cerebro del local
          </h2>
          <p className="mt-4 max-w-sm text-sm text-primary-foreground/70">
            Comandas, cobros y tu copiloto en español — todo tu local en un solo lugar.
          </p>
          <ul className="mt-6 flex flex-col gap-2 text-sm text-primary-foreground/80">
            <li>· Comandas y cocina (KDS)</li>
            <li>· Cobros con MercadoPago</li>
            <li>· Reportes y asesor en pesos</li>
          </ul>
        </div>

        <div className="relative text-xs text-primary-foreground/50">© Wellnod</div>
      </aside>

      <main className="flex items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm">
          <div className="mb-6 flex flex-col gap-1">
            <GradientHeading size="sm" weight="bold">
              {title}
            </GradientHeading>
            {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
          </div>
          {children}
          {footer ? (
            <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>
          ) : null}
        </div>
      </main>
    </div>
  )
}
