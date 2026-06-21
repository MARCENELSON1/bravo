import type { ComponentType } from "react"
import {
  ArrowRight,
  ChefHat,
  CreditCard,
  Receipt,
  TrendingUp,
  UtensilsCrossed,
  Wallet,
} from "lucide-react"
import { Link } from "react-router-dom"

import { GradientHeading } from "@/components/ui/gradient-heading"
import {
  TextureCard,
  TextureCardContent,
  TextureCardHeader,
  TextureCardTitle,
} from "@/components/ui/texture-card"

interface Kpi {
  label: string
  value: string
  hint: string
  icon: ComponentType<{ className?: string }>
}

const KPIS: Kpi[] = [
  { label: "Ventas de hoy", value: "—", hint: "Cobrado del día", icon: TrendingUp },
  { label: "Comandas activas", value: "—", hint: "En curso", icon: UtensilsCrossed },
  { label: "Ticket promedio", value: "—", hint: "Por comanda", icon: CreditCard },
  { label: "Egresos de hoy", value: "—", hint: "Salidas del día", icon: Receipt },
  { label: "Neto", value: "—", hint: "Ventas − egresos", icon: Wallet },
]

const SHORTCUTS = [
  { label: "Ir a Mesas", to: "/app/floor", icon: UtensilsCrossed },
  { label: "Cocina (KDS)", to: "/app/kds", icon: ChefHat },
  { label: "Registrar egreso", to: "/app/expenses", icon: Receipt },
]

export function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="lg" weight="bold">
          Resumen
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          Tu local de un vistazo. Las métricas en vivo llegan con los reportes.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {KPIS.map((kpi) => (
          <TextureCard key={kpi.label}>
            <TextureCardHeader className="flex flex-row items-center justify-between px-5 pt-5">
              <TextureCardTitle className="text-sm font-medium text-muted-foreground">
                {kpi.label}
              </TextureCardTitle>
              <kpi.icon className="size-4 text-muted-foreground" />
            </TextureCardHeader>
            <TextureCardContent className="px-5 pb-5 pt-1">
              <div className="text-3xl font-semibold tabular-nums text-foreground">
                {kpi.value}
              </div>
              <p className="text-xs text-muted-foreground">{kpi.hint}</p>
            </TextureCardContent>
          </TextureCard>
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-muted-foreground">Accesos rápidos</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {SHORTCUTS.map((shortcut) => (
            <Link
              key={shortcut.to}
              to={shortcut.to}
              className="group flex items-center justify-between rounded-2xl border border-border bg-card p-4 text-sm font-medium transition-colors hover:bg-accent"
            >
              <span className="flex items-center gap-2">
                <shortcut.icon className="size-4 text-muted-foreground" />
                {shortcut.label}
              </span>
              <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
