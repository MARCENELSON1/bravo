import type { ReactNode } from "react"
import { Check } from "lucide-react"

import { Reveal } from "@/presentation/components/ui/reveal"
import { cn } from "@/presentation/lib/cn"

export function Showcase() {
  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-20 px-5 py-20 md:gap-28 md:py-24">
      <ShowcaseRow
        eyebrow="Operación"
        title="Del pedido a la cocina, sin fricción"
        description="El mozo carga la comanda en la mesa y llega sola a cocina y barra. Cada estación ve lo suyo, ordenado por tiempo. Menos errores, salida más rápida."
        bullets={["Comandas desde el celular", "KDS por estación", "Estados en tiempo real"]}
        visual={<OrderVisual />}
      />
      <ShowcaseRow
        reverse
        eyebrow="Decisiones"
        title="Preguntale a tu negocio, en español"
        description="El copiloto responde con datos reales de tu local: ventas, márgenes, stock y horarios. Sin armar reportes ni pelearte con planillas."
        bullets={["Respuestas en lenguaje natural", "Reportes en pesos y en vivo", "Sugerencias accionables"]}
        visual={<CopilotVisual />}
      />
    </section>
  )
}

function ShowcaseRow({
  reverse,
  eyebrow,
  title,
  description,
  bullets,
  visual,
}: {
  reverse?: boolean
  eyebrow: string
  title: string
  description: string
  bullets: string[]
  visual: ReactNode
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-10 lg:flex-row lg:items-center lg:gap-16",
        reverse && "lg:flex-row-reverse",
      )}
    >
      <Reveal className="flex-1">
        <p className="text-sm font-semibold uppercase tracking-wider text-primary">{eyebrow}</p>
        <h3 className="mt-3 font-display text-2xl font-bold tracking-tight text-balance sm:text-3xl">
          {title}
        </h3>
        <p className="mt-4 text-muted-foreground">{description}</p>
        <ul className="mt-6 flex flex-col gap-2.5">
          {bullets.map((bullet) => (
            <li key={bullet} className="flex items-center gap-2.5 text-sm">
              <Check className="size-4 shrink-0 text-primary" />
              {bullet}
            </li>
          ))}
        </ul>
      </Reveal>
      <Reveal className="flex-1" style={{ transitionDelay: "100ms" }}>
        {visual}
      </Reveal>
    </div>
  )
}

function OrderVisual() {
  const items = [
    { qty: "2", name: "Milanesa napolitana", station: "Cocina" },
    { qty: "1", name: "Papas fritas", station: "Cocina" },
    { qty: "3", name: "Cerveza IPA", station: "Barra" },
  ]
  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-xl shadow-primary/5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">Mesa 7 · Comanda #128</p>
          <p className="font-medium">En preparación</p>
        </div>
        <span className="rounded-full bg-primary/12 px-2.5 py-1 text-xs font-medium text-primary">
          04:12
        </span>
      </div>
      <ul className="mt-4 flex flex-col gap-2">
        {items.map((item) => (
          <li
            key={item.name}
            className="flex items-center justify-between rounded-xl bg-muted px-3 py-2.5 text-sm"
          >
            <span className="flex items-center gap-2">
              <span className="flex size-6 items-center justify-center rounded-md bg-primary/15 text-xs font-semibold text-primary">
                {item.qty}
              </span>
              {item.name}
            </span>
            <span className="text-xs text-muted-foreground">{item.station}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function CopilotVisual() {
  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-xl shadow-primary/5">
      <div className="grid grid-cols-3 gap-3">
        {[
          { l: "Ventas hoy", v: "$482k" },
          { l: "Margen", v: "63%" },
          { l: "Comandas", v: "37" },
        ].map((kpi) => (
          <div key={kpi.l} className="rounded-xl bg-muted px-3 py-3">
            <p className="text-[11px] text-muted-foreground">{kpi.l}</p>
            <p className="mt-0.5 font-semibold tabular-nums">{kpi.v}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-col gap-2">
        <p className="ml-auto max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm text-primary-foreground">
          ¿Qué plato dejó más margen esta semana?
        </p>
        <p className="mr-auto max-w-[85%] rounded-2xl rounded-bl-sm bg-muted px-3.5 py-2 text-sm">
          La milanesa napolitana: 71% de margen y 48 unidades vendidas. ¿La destaco en el menú?
        </p>
      </div>
    </div>
  )
}
