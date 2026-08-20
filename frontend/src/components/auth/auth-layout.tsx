import type { ReactNode } from "react"
import { motion } from "motion/react"

import { WellnodMark } from "@/components/brand/wellnod-mark"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { useReduceMotion } from "@/lib/reduce-motion"

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
  const reduce = useReduceMotion()
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <aside
        className="relative isolate hidden flex-col justify-between overflow-hidden bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)] p-10 text-white lg:flex"
      >
        {/* imagen como textura sobre el gradiente verde: mismo tratamiento y color
            que el fondo principal de la app (soft-light + grano) */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light"
          style={{ backgroundImage: "url('/login-bg.png')" }}
        />
        <div
          aria-hidden
          className="bg-grain pointer-events-none absolute inset-0 opacity-[0.18] mix-blend-overlay"
        />
        {/* oscurecido leve para legibilidad del texto */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-black/25 via-transparent to-black/40"
        />

        <div className="relative mt-1 flex items-center gap-3">
          <WellnodMark className="h-11 w-auto shrink-0 text-white/90" />
          <span className="font-heading translate-y-0.5 text-3xl leading-none">
            <span className="font-bold">Well</span>
            <span className="-ml-[3px] font-light text-white/70">nod</span>
          </span>
        </div>

        <div className="relative">
          <h2 className="font-heading text-4xl font-semibold leading-tight">
            El cerebro del local
          </h2>
          <p className="mt-4 max-w-sm text-sm text-white/70">
            Todo lo que necesitás para entender y gestionar tu negocio, en un solo lugar.
          </p>
          <ul className="mt-6 flex flex-col gap-2 text-sm text-white/80">
            <li>Información y datos en tiempo real</li>
            <li>Todas las áreas: comandas, cobros, personal y más</li>
            <li>IA Insights: Copiloto y Diagnóstico de tu negocio</li>
          </ul>
        </div>

        <div className="relative text-xs text-white/50">© Wellnod</div>
      </aside>

      <main className="flex items-center justify-center bg-background p-6">
        <motion.div
          className="w-full max-w-sm"
          initial={reduce ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduce ? { duration: 0 } : { duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
        >
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
        </motion.div>
      </main>
    </div>
  )
}
