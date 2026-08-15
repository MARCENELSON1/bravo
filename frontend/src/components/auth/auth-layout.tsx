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
      <aside
        className="relative hidden flex-col justify-between overflow-hidden bg-cover bg-center p-10 text-white lg:flex"
        style={{ backgroundImage: "url('/app-bg.png')" }}
      >
        {/* overlay para legibilidad del texto sobre la foto */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-black/45 via-black/25 to-black/55"
        />

        <div className="relative flex items-center gap-2">
          <WellnodMark className="h-8 w-auto text-white/90" />
          <span className="font-heading text-lg tracking-tight">
            <span className="font-bold">Well</span>
            <span className="font-light text-white/70">nod</span>
          </span>
        </div>

        <div className="relative">
          <h2 className="font-heading text-4xl font-semibold leading-tight">
            El cerebro del local
          </h2>
          <p className="mt-4 max-w-sm text-sm text-white/70">
            Comandas, cobros y tu copiloto en español — todo tu local en un solo lugar.
          </p>
          <ul className="mt-6 flex flex-col gap-2 text-sm text-white/80">
            <li>· Comandas y cocina (KDS)</li>
            <li>· Cobros con MercadoPago</li>
            <li>· Reportes y asesor en pesos</li>
          </ul>
        </div>

        <div className="relative text-xs text-white/50">© Wellnod</div>
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
