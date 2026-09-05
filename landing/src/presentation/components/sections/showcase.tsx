import type { ReactNode } from "react"
import { Check } from "lucide-react"

import { Reveal, Stagger } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"
import type { Locale } from "@/domain/value-objects/region"
import { cn } from "@/presentation/lib/cn"

const COPY = {
  "es-AR": {
    row1: {
      eyebrow: "Operación",
      title: "Del pedido a la cocina, sin fricción",
      description:
        "El mozo carga la comanda en la mesa y llega sola a cocina y barra. Cada estación ve lo suyo, ordenado por tiempo. Menos errores, salida más rápida.",
      bullets: ["Comandas desde el celular", "KDS por estación", "Estados en tiempo real"],
    },
    row2: {
      eyebrow: "Decisiones",
      title: "Preguntale a tu negocio",
      description:
        "El copiloto responde con datos reales de tu local: ventas, márgenes, stock y horarios. Sin armar reportes ni pelearte con planillas.",
      bullets: ["Respuestas en lenguaje natural", "Reportes en pesos y en vivo", "Sugerencias accionables"],
    },
    order: {
      table: "Mesa 7 · Comanda #128",
      status: "En preparación",
      items: [
        { qty: "2", name: "Milanesa napolitana", station: "Cocina" },
        { qty: "1", name: "Papas fritas", station: "Cocina" },
        { qty: "3", name: "Cerveza IPA", station: "Barra" },
      ],
    },
    copilot: {
      kpis: [
        { l: "Ventas hoy", v: "$482k" },
        { l: "Margen", v: "63%" },
        { l: "Comandas", v: "37" },
      ],
      question: "¿Qué plato dejó más margen esta semana?",
      answer: "La milanesa napolitana: 71% de margen y 48 unidades vendidas. ¿La destaco en el menú?",
    },
  },
  "en-US": {
    row1: {
      eyebrow: "Operations",
      title: "From order to kitchen, without friction",
      description:
        "Your server enters the order at the table and it lands in the kitchen and bar on its own. Each station sees its own tickets, sorted by time. Fewer mistakes, faster service.",
      bullets: ["Orders from a phone", "KDS by station", "Real-time status"],
    },
    row2: {
      eyebrow: "Decisions",
      title: "Ask your business",
      description:
        "The copilot answers with your real data: sales, margins, stock, and hours. No reports to build, no spreadsheets to fight.",
      bullets: ["Answers in plain language", "Live reports in dollars", "Actionable suggestions"],
    },
    order: {
      table: "Table 7 · Order #128",
      status: "In progress",
      items: [
        { qty: "2", name: "Cheeseburger", station: "Kitchen" },
        { qty: "1", name: "French fries", station: "Kitchen" },
        { qty: "3", name: "IPA", station: "Bar" },
      ],
    },
    copilot: {
      kpis: [
        { l: "Sales today", v: "$4,820" },
        { l: "Margin", v: "63%" },
        { l: "Orders", v: "37" },
      ],
      question: "Which dish had the best margin this week?",
      answer: "The cheeseburger: 71% margin and 48 sold. Want me to feature it on the menu?",
    },
  },
} as const

export function Showcase() {
  const locale = useContainer().locale
  const t = COPY[locale]

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-28 px-5 py-28 md:gap-40 md:py-36">
      <ShowcaseRow
        eyebrow={t.row1.eyebrow}
        title={t.row1.title}
        description={t.row1.description}
        bullets={t.row1.bullets}
        visual={<OrderVisual locale={locale} />}
      />
      <ShowcaseRow
        reverse
        eyebrow={t.row2.eyebrow}
        title={t.row2.title}
        description={t.row2.description}
        bullets={t.row2.bullets}
        visual={<CopilotVisual locale={locale} />}
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
  bullets: readonly string[]
  visual: ReactNode
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-12 lg:flex-row lg:items-start lg:gap-20",
        reverse && "lg:flex-row-reverse",
      )}
    >
      <Reveal className="flex-1 lg:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
        <h3 className="mt-4 font-display text-3xl font-bold leading-[1.08] tracking-tight text-balance sm:text-4xl">
          {title}
        </h3>
        <p className="mt-5 text-lg leading-relaxed text-muted-foreground">{description}</p>
        <Stagger as="ul" className="mt-8 flex flex-col gap-3.5">
          {bullets.map((bullet) => (
            <li key={bullet} className="flex items-center gap-3 text-[0.95rem]">
              <Check className="size-4 shrink-0 text-primary" />
              {bullet}
            </li>
          ))}
        </Stagger>
      </Reveal>
      {/* El visual queda fijo mientras el texto pasa al lado. Solo en escritorio:
          en móvil las columnas se apilan y no hay recorrido que acompañar. */}
      <Reveal anim="scale" delay={120} className="flex-1 lg:sticky lg:top-28">
        {visual}
      </Reveal>
    </div>
  )
}

function OrderVisual({ locale }: { locale: Locale }) {
  const { order } = COPY[locale]
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{order.table}</p>
          <p className="font-medium">{order.status}</p>
        </div>
        <span className="rounded-full bg-primary/12 px-2.5 py-1 text-xs font-medium text-primary">
          04:12
        </span>
      </div>
      <Stagger as="ul" className="mt-5 flex flex-col gap-2">
        {order.items.map((item) => (
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
      </Stagger>
    </div>
  )
}

function CopilotVisual({ locale }: { locale: Locale }) {
  const { copilot } = COPY[locale]
  return (
    <div className="rounded-2xl border border-border/70 bg-card p-6">
      <div className="grid grid-cols-3 gap-3">
        {copilot.kpis.map((kpi) => (
          <div key={kpi.l} className="rounded-xl bg-muted px-3 py-3">
            <p className="text-[11px] text-muted-foreground">{kpi.l}</p>
            <p className="mt-0.5 font-semibold tabular-nums">{kpi.v}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-col gap-2">
        <p className="ml-auto max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm text-primary-foreground">
          {copilot.question}
        </p>
        <p className="mr-auto max-w-[85%] rounded-2xl rounded-bl-sm bg-muted px-3.5 py-2 text-sm">
          {copilot.answer}
        </p>
      </div>
    </div>
  )
}
