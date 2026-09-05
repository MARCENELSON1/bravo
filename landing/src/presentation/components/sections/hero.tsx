import { useEffect, useRef, useState, type Ref, type ReactNode } from "react"
import {
  Calculator,
  ChefHat,
  Coins,
  FileText,
  Home,
  Lightbulb,
  LineChart,
  Menu,
  Package,
  QrCode,
  Sparkles,
  UtensilsCrossed,
  Users,
} from "lucide-react"

import { WellnodMark } from "@/presentation/components/brand/wellnod-mark"
import { useContainer } from "@/presentation/providers/container-provider"
import type { Locale } from "@/domain/value-objects/region"
import { cn } from "@/presentation/lib/cn"

// ── Localización ──────────────────────────────────────────────────────────────
// Todo el texto visible del hero interactivo vive acá, por locale. ES = paridad
// (idéntico a lo shippeado en AR). EN = transcreación US: ARCA/AFIP → sales tax,
// MercadoPago → Stripe/cards, Copiloto en español → Copilot in English, pesos → USD.
type Tone = "green" | "amber" | "red" | "muted"
type Col = { h: string; right?: boolean }
type Kpi = { l: string; v: string }
type Channel = { m: string; w: string }
type FinCard = { l: string; v: string; dot: string; act: string }
type Reservation = {
  time: string
  guest: string
  party: string
  service: string
  table: string
  status: string
  tone: Tone
}
type Product = {
  name: string
  price: string
  keep: string
  sold: string
  status: string
  tone: Tone
}
type PayRow = { method: string; type: string; ops: string; amount: string }
type Qa = { q: string; a: ReactNode }

type Copy = {
  titleBefore: string
  titleHighlight: string
  subtitle: string
  navMain: {
    home: string
    finance: string
    customers: string
    products: string
    insights: string
    advisor: string
    reports: string
  }
  navOps: {
    tables: string
    kitchen: string
    register: string
    tips: string
    clockin: string
  }
  opsLabel: string
  ownerName: string
  ownerRole: string
  ownerInitials: string
  venue: string
  clock: string
  onShift: string
  ranges: string[]
  inicio: {
    profitLabel: string
    profitValue: string
    delta: string
    kpis: Kpi[]
    channelsTitle: string
    channels: Channel[]
  }
  finanzas: {
    title: string
    netLabel: string
    netValue: string
    netDelta: string
    cards: FinCard[]
  }
  clientes: {
    title: string
    subtitle: string
    newBtn: string
    cols: Col[]
    rows: Reservation[]
  }
  productos: {
    title: string
    subtitle: string
    cols: Col[]
    rows: Product[]
  }
  reportes: {
    title: string
    kpis: Kpi[]
    mixTitle: string
    cols: Col[]
    rows: PayRow[]
  }
  asesor: {
    title: string
    subtitle: string
    monthChip: string
    configCosts: string
    bannerBefore: string
    bannerCopilot: string
    bannerAfter: string
    summary: ReactNode
    kpis: Kpi[]
  }
  copilot: {
    title: string
    subtitle: string
    askBtn: string
    demoNote: string
    qa: Qa[]
  }
}

const COPY: Record<Locale, Copy> = {
  "es-AR": {
    titleBefore: "Todo tu restaurante, ",
    titleHighlight: "en una sola app",
    subtitle:
      "Operás, cobrás y facturás en un solo lugar — con un copiloto que responde lo que le preguntás y un asesor que te da recomendaciones en base a cómo va tu negocio.",
    navMain: {
      home: "Inicio",
      finance: "Finanzas",
      customers: "Clientes",
      products: "Productos",
      insights: "IA Insights",
      advisor: "Asesor",
      reports: "Reportes",
    },
    navOps: {
      tables: "Mesas",
      kitchen: "Cocina",
      register: "Caja",
      tips: "Propinas",
      clockin: "Fichar",
    },
    opsLabel: "Operación",
    ownerName: "Juan Pérez",
    ownerRole: "Dueño",
    ownerInitials: "JP",
    venue: "Restaurante Villa Paz",
    clock: "14:32",
    onShift: "En turno",
    ranges: ["Hoy", "Semana", "Mes", "Año"],
    inicio: {
      profitLabel: "Tu ganancia de hoy",
      profitValue: "$386.300",
      delta: "Vas 18% arriba de ayer ↑",
      kpis: [
        { l: "Facturaste hoy", v: "$482.500" },
        { l: "Gastaste hoy", v: "$96.200" },
        { l: "Tu margen hoy", v: "$386.300" },
      ],
      channelsTitle: "Cobros de hoy por canal",
      channels: [
        { m: "MercadoPago", w: "72%" },
        { m: "Efectivo", w: "18%" },
        { m: "Tarjeta", w: "10%" },
      ],
    },
    finanzas: {
      title: "Finanzas",
      netLabel: "Tu ganancia neta del período",
      netValue: "$612.300",
      netDelta: "▲ $84.200 vs período anterior",
      cards: [
        { l: "Margen neto", v: "$612k", dot: "bg-emerald-500", act: "Mantener" },
        { l: "Food cost", v: "34%", dot: "bg-amber-500", act: "Revisar" },
        { l: "Costo de personal", v: "$410k", dot: "bg-emerald-500", act: "Mantener" },
        { l: "Mermas", v: "$58k", dot: "bg-red-500", act: "Actuar" },
      ],
    },
    clientes: {
      title: "Reservas",
      subtitle: "Agenda del servicio por día y turno.",
      newBtn: "Nueva reserva",
      cols: [
        { h: "Hora" },
        { h: "Cliente" },
        { h: "Personas", right: true },
        { h: "Turno" },
        { h: "Mesa" },
        { h: "Estado" },
      ],
      rows: [
        { time: "20:30", guest: "Familia Gómez", party: "4", service: "Cena", table: "Mesa 7", status: "Confirmada", tone: "green" },
        { time: "21:00", guest: "Laura Díaz", party: "2", service: "Cena", table: "Mesa 3", status: "Sentada", tone: "muted" },
        { time: "21:15", guest: "Grupo Empresa", party: "8", service: "Cena", table: "Salón", status: "Confirmada", tone: "green" },
        { time: "13:30", guest: "Martín Ruiz", party: "3", service: "Almuerzo", table: "Mesa 5", status: "No-show", tone: "red" },
      ],
    },
    productos: {
      title: "Productos",
      subtitle: "Tu catálogo y precios.",
      cols: [
        { h: "Nombre" },
        { h: "Precio", right: true },
        { h: "Te deja", right: true },
        { h: "Vendidos", right: true },
        { h: "Estado" },
      ],
      rows: [
        { name: "Milanesa napolitana", price: "$8.900", keep: "$6.340 · 71%", sold: "128", status: "Activo", tone: "green" },
        { name: "Papas fritas", price: "$3.500", keep: "$2.480 · 71%", sold: "96", status: "Activo", tone: "green" },
        { name: "IPA Artesanal", price: "$2.800", keep: "$1.900 · 68%", sold: "84", status: "Activo", tone: "green" },
        { name: "Ojo de bife", price: "$12.400", keep: "$7.100 · 57%", sold: "41", status: "Activo", tone: "green" },
        { name: "Flan casero", price: "$2.200", keep: "$1.540 · 70%", sold: "38", status: "Inactivo", tone: "muted" },
      ],
    },
    reportes: {
      title: "Reportes",
      kpis: [
        { l: "Ventas", v: "$2,48M" },
        { l: "Cobrado", v: "$2,41M" },
        { l: "Egresos", v: "$1,87M" },
        { l: "Margen bruto", v: "$1,02M" },
        { l: "Ticket promedio", v: "$13,2k" },
        { l: "Food cost", v: "34%" },
      ],
      mixTitle: "Mix de medios de pago",
      cols: [
        { h: "Medio" },
        { h: "Tipo" },
        { h: "Operaciones", right: true },
        { h: "Monto", right: true },
      ],
      rows: [
        { method: "MercadoPago", type: "Ingreso", ops: "142", amount: "$1,78M" },
        { method: "Efectivo", type: "Ingreso", ops: "38", amount: "$446k" },
        { method: "Tarjeta", type: "Ingreso", ops: "21", amount: "$248k" },
      ],
    },
    asesor: {
      title: "Asesor",
      subtitle: "Cómo te fue y qué hacer. Por defecto, este mes.",
      monthChip: "Jul 2026",
      configCosts: "Configurar costos",
      bannerBefore: "¿Querés preguntarle a tu negocio? Probá el ",
      bannerCopilot: "Copiloto",
      bannerAfter: " en IA Insights →",
      summary: (
        <>
          Vendiste <b>$2.480.900</b> este mes, un <b className="text-primary">18% más</b>. Tu margen
          neto va en <b>$612.300</b> — sólido, pero el food cost de cocina está alto.
        </>
      ),
      kpis: [
        { l: "Ventas", v: "$2,48M" },
        { l: "Margen bruto", v: "$1,02M" },
        { l: "Margen neto", v: "$612k" },
        { l: "Food cost", v: "34%" },
        { l: "Prime cost", v: "58%" },
        { l: "Punto de equilibrio", v: "$1,9M" },
      ],
    },
    copilot: {
      title: "Copiloto",
      subtitle: "Preguntá sobre tu negocio. Te muestro la respuesta y de dónde sale.",
      askBtn: "Preguntar",
      demoNote:
        "A modo de ejemplo, con datos de demo. En Wellnod el Copiloto responde con los números reales de tu local.",
      qa: [
        {
          q: "¿Cuánto vendí este mes?",
          a: (
            <>
              Vendiste <b>$2.480.900</b> este mes — un <b className="text-primary">18% más</b> que el
              mes pasado.
            </>
          ),
        },
        {
          q: "¿Mis 5 más vendidos?",
          a: (
            <>
              Milanesa napolitana, papas, IPA, ojo de bife y flan casero — juntos, el <b>41%</b> de
              tus ventas.
            </>
          ),
        },
        {
          q: "¿Qué mozo facturó más?",
          a: (
            <>
              Sofía, con <b>$412.300</b> en 87 mesas — el <b className="text-primary">22%</b> del
              salón.
            </>
          ),
        },
        {
          q: "¿Reservas de mañana?",
          a: (
            <>
              Tenés <b>14 reservas</b> (38 cubiertos), la mayoría entre las 21 y 22 h.
            </>
          ),
        },
        {
          q: "¿Mi hora pico?",
          a: (
            <>
              Viernes y sábados de <b>21 a 23 h</b>: ahí se concentra el{" "}
              <b className="text-primary">34%</b> de tus ventas de la semana.
            </>
          ),
        },
        {
          q: "¿Ticket promedio?",
          a: (
            <>
              <b>$4.740</b> por mesa — un <b className="text-primary">6% más</b> que el mes pasado.
            </>
          ),
        },
        {
          q: "¿Qué stock me falta?",
          a: (
            <>
              Muzzarella y papas: al ritmo de esta semana te alcanzan para <b>3 días</b>.
            </>
          ),
        },
      ],
    },
  },
  "en-US": {
    titleBefore: "Your whole restaurant, ",
    titleHighlight: "in one app",
    subtitle:
      "Take orders, get paid, and stay tax-ready in one place — with a copilot that answers whatever you ask and an advisor that gives you recommendations based on how your business is doing.",
    navMain: {
      home: "Home",
      finance: "Finance",
      customers: "Customers",
      products: "Products",
      insights: "AI Insights",
      advisor: "Advisor",
      reports: "Reports",
    },
    navOps: {
      tables: "Tables",
      kitchen: "Kitchen",
      register: "Register",
      tips: "Tips",
      clockin: "Clock in",
    },
    opsLabel: "Operations",
    ownerName: "John Smith",
    ownerRole: "Owner",
    ownerInitials: "JS",
    venue: "Villa Paz Bistro",
    clock: "2:32 PM",
    onShift: "On shift",
    ranges: ["Today", "Week", "Month", "Year"],
    inicio: {
      profitLabel: "Your profit today",
      profitValue: "$38,630",
      delta: "Up 18% from yesterday ↑",
      kpis: [
        { l: "Billed today", v: "$48,250" },
        { l: "Spent today", v: "$9,620" },
        { l: "Your margin today", v: "$38,630" },
      ],
      channelsTitle: "Today's payments by channel",
      channels: [
        { m: "Stripe", w: "72%" },
        { m: "Cash", w: "18%" },
        { m: "Card", w: "10%" },
      ],
    },
    finanzas: {
      title: "Finance",
      netLabel: "Your net profit for the period",
      netValue: "$61,230",
      netDelta: "▲ $8,420 vs previous period",
      cards: [
        { l: "Net margin", v: "$61.2k", dot: "bg-emerald-500", act: "On track" },
        { l: "Food cost", v: "34%", dot: "bg-amber-500", act: "Review" },
        { l: "Labor cost", v: "$41k", dot: "bg-emerald-500", act: "On track" },
        { l: "Waste", v: "$5.8k", dot: "bg-red-500", act: "Act now" },
      ],
    },
    clientes: {
      title: "Reservations",
      subtitle: "Service schedule by day and seating.",
      newBtn: "New reservation",
      cols: [
        { h: "Time" },
        { h: "Guest" },
        { h: "Party", right: true },
        { h: "Service" },
        { h: "Table" },
        { h: "Status" },
      ],
      rows: [
        { time: "7:30 PM", guest: "Miller party", party: "4", service: "Dinner", table: "Table 7", status: "Confirmed", tone: "green" },
        { time: "9:00 PM", guest: "Laura Bennett", party: "2", service: "Dinner", table: "Table 3", status: "Seated", tone: "muted" },
        { time: "9:15 PM", guest: "Corporate group", party: "8", service: "Dinner", table: "Main room", status: "Confirmed", tone: "green" },
        { time: "1:30 PM", guest: "Martin Reed", party: "3", service: "Lunch", table: "Table 5", status: "No-show", tone: "red" },
      ],
    },
    productos: {
      title: "Products",
      subtitle: "Your catalog and prices.",
      cols: [
        { h: "Name" },
        { h: "Price", right: true },
        { h: "You keep", right: true },
        { h: "Sold", right: true },
        { h: "Status" },
      ],
      rows: [
        { name: "Classic cheeseburger", price: "$14.50", keep: "$10.30 · 71%", sold: "128", status: "Active", tone: "green" },
        { name: "French fries", price: "$6.00", keep: "$4.25 · 71%", sold: "96", status: "Active", tone: "green" },
        { name: "Craft IPA", price: "$8.00", keep: "$5.45 · 68%", sold: "84", status: "Active", tone: "green" },
        { name: "Ribeye steak", price: "$32.00", keep: "$18.20 · 57%", sold: "41", status: "Active", tone: "green" },
        { name: "House cheesecake", price: "$9.00", keep: "$6.30 · 70%", sold: "38", status: "Inactive", tone: "muted" },
      ],
    },
    reportes: {
      title: "Reports",
      kpis: [
        { l: "Sales", v: "$248k" },
        { l: "Collected", v: "$241k" },
        { l: "Expenses", v: "$187k" },
        { l: "Gross margin", v: "$102k" },
        { l: "Avg. check", v: "$58" },
        { l: "Food cost", v: "34%" },
      ],
      mixTitle: "Payment method mix",
      cols: [
        { h: "Method" },
        { h: "Type" },
        { h: "Transactions", right: true },
        { h: "Amount", right: true },
      ],
      rows: [
        { method: "Stripe", type: "Income", ops: "142", amount: "$178k" },
        { method: "Cash", type: "Income", ops: "38", amount: "$44.6k" },
        { method: "Card", type: "Income", ops: "21", amount: "$24.8k" },
      ],
    },
    asesor: {
      title: "Advisor",
      subtitle: "How you did and what to do. This month by default.",
      monthChip: "Jul 2026",
      configCosts: "Configure costs",
      bannerBefore: "Want to ask your business a question? Try the ",
      bannerCopilot: "Copilot",
      bannerAfter: " in AI Insights →",
      summary: (
        <>
          You sold <b>$248,090</b> this month, <b className="text-primary">up 18%</b>. Your net margin
          is at <b>$61,230</b> — solid, but kitchen food cost is running high.
        </>
      ),
      kpis: [
        { l: "Sales", v: "$248k" },
        { l: "Gross margin", v: "$102k" },
        { l: "Net margin", v: "$61.2k" },
        { l: "Food cost", v: "34%" },
        { l: "Prime cost", v: "58%" },
        { l: "Break-even", v: "$190k" },
      ],
    },
    copilot: {
      title: "Copilot",
      subtitle: "Ask about your business. I show you the answer and where it comes from.",
      askBtn: "Ask",
      demoNote:
        "Example only, with demo data. In Wellnod the Copilot answers with your location's real numbers.",
      qa: [
        {
          q: "How much did I sell this month?",
          a: (
            <>
              You sold <b>$248,090</b> this month — <b className="text-primary">up 18%</b> from last
              month.
            </>
          ),
        },
        {
          q: "My top 5 sellers?",
          a: (
            <>
              Cheeseburger, fries, IPA, ribeye and cheesecake — together, <b>41%</b> of your sales.
            </>
          ),
        },
        {
          q: "Which server sold the most?",
          a: (
            <>
              Sofia, with <b>$41,230</b> across 87 tables — <b className="text-primary">22%</b> of the
              floor.
            </>
          ),
        },
        {
          q: "Tomorrow's reservations?",
          a: (
            <>
              You have <b>14 reservations</b> (38 covers), most between 9 and 10 PM.
            </>
          ),
        },
        {
          q: "My peak hours?",
          a: (
            <>
              Friday and Saturday from <b>9 to 11 PM</b>: that's{" "}
              <b className="text-primary">34%</b> of your weekly sales.
            </>
          ),
        },
        {
          q: "Average check?",
          a: (
            <>
              <b>$58</b> per table — <b className="text-primary">up 6%</b> from last month.
            </>
          ),
        },
        {
          q: "What am I running low on?",
          a: (
            <>
              Mozzarella and potatoes: at this week's pace, you have about <b>3 days</b> left.
            </>
          ),
        },
      ],
    },
  },
}

// Ítems de navegación con id ESTABLE (independiente del idioma): el estado de la
// pantalla y el switch se manejan por id, y la etiqueta visible sale de COPY.
type MainId = keyof Copy["navMain"]
type OpsId = keyof Copy["navOps"]
const NAV_MAIN: { id: MainId; icon: typeof Home }[] = [
  { id: "home", icon: Home },
  { id: "finance", icon: LineChart },
  { id: "customers", icon: Users },
  { id: "products", icon: Package },
  { id: "insights", icon: Lightbulb },
  { id: "advisor", icon: Sparkles },
  { id: "reports", icon: FileText },
]
const NAV_OPS: { id: OpsId; icon: typeof Home }[] = [
  { id: "tables", icon: UtensilsCrossed },
  { id: "kitchen", icon: ChefHat },
  { id: "register", icon: Calculator },
  { id: "tips", icon: Coins },
  { id: "clockin", icon: QrCode },
]

export function Hero() {
  const locale = useContainer().locale
  const t = COPY[locale]

  return (
    <section id="top" className="relative overflow-hidden">
      {/* Glow verde de fondo */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-32 left-1/2 h-[38rem] w-[90%] -translate-x-1/2 rounded-[50%] bg-primary/20 blur-[140px]" />
      </div>

      {/* Título grande, centrado, con animación de entrada */}
      <div className="mx-auto max-w-6xl px-5 pt-20 text-center md:pt-28">
        <h1
          className="hero-title font-display text-6xl font-bold leading-[1.02] tracking-tight text-balance sm:text-7xl lg:text-8xl"
          style={{ animationDelay: "0ms" }}
        >
          {t.titleBefore}
          <span className="text-primary">{t.titleHighlight}</span>.
        </h1>
        <p
          className="hero-anim mx-auto mt-5 max-w-3xl text-lg text-balance text-muted-foreground sm:text-xl"
          style={{ animationDelay: "90ms" }}
        >
          {t.subtitle}
        </p>
      </div>

      {/* Pantalla interactiva de Wellnod */}
      <div className="hero-screen relative mx-auto mt-8 max-w-7xl px-4" style={{ animationDelay: "300ms" }}>
        <AppMockup locale={locale} />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-28 bg-gradient-to-b from-transparent to-background"
        />
      </div>
    </section>
  )
}

// Réplica interactiva del interfaz de Wellnod, con el contenido real de cada sección.
function AppMockup({ locale }: { locale: Locale }) {
  const t = COPY[locale]
  const reduced = prefersReducedMotion()
  const rootRef = useRef<HTMLDivElement>(null)
  const asesorNavRef = useRef<HTMLButtonElement>(null)
  const tryCopilotRef = useRef<HTMLButtonElement>(null)

  // El estado de pantalla usa el id estable (no la etiqueta traducida).
  const [screen, setScreen] = useState<MainId>(reduced ? "advisor" : "home")
  const [cursor, setCursor] = useState({ x: 0, y: 0, visible: false, snap: true, press: false })

  const started = useRef(false)
  const cancelled = useRef(false)
  const timers = useRef<number[]>([])

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t))
    timers.current = []
  }
  // Programa un paso del tour (se saltea si el usuario ya interactuó).
  const at = (ms: number, fn: () => void) => {
    timers.current.push(window.setTimeout(() => !cancelled.current && fn(), ms))
  }
  // Punto (relativo a la raíz) al que apunta la punta del cursor sobre un elemento.
  const pointAt = (el: HTMLElement | null) => {
    const root = rootRef.current
    if (!root || !el) return null
    const r = root.getBoundingClientRect()
    const b = el.getBoundingClientRect()
    return { x: b.left - r.left + Math.min(22, b.width * 0.35), y: b.top - r.top + b.height / 2 }
  }

  // Tour guiado (una vez, al entrar en viewport): Inicio → click en Asesor → click
  // en el banner del Copiloto → IA Insights → el cursor va hasta "Preguntar" y
  // desaparece, para que la persona entienda que tiene que tocarlo.
  const runDemo = () => {
    // 1) Aparece junto a "Asesor" y hace click → pantalla Asesor.
    at(150, () => {
      const p = pointAt(asesorNavRef.current)
      if (p) setCursor({ x: p.x + 34, y: p.y + 24, visible: true, snap: true, press: false })
    })
    at(450, () => {
      const p = pointAt(asesorNavRef.current)
      if (p) setCursor({ x: p.x, y: p.y, visible: true, snap: false, press: false })
    })
    at(1200, () => setCursor((c) => ({ ...c, press: true })))
    at(1450, () => {
      setCursor((c) => ({ ...c, press: false }))
      setScreen("advisor")
    })
    // 2) Se queda un rato en Asesor (que la persona lo lea) y lleva el cursor hasta
    //    el banner del Copiloto, donde desaparece SIN clickear: la persona tiene que
    //    tocarlo para entrar a IA Insights.
    at(3150, () => {
      const p = pointAt(tryCopilotRef.current)
      if (p) setCursor((c) => ({ ...c, x: p.x, y: p.y, snap: false }))
    })
    at(4200, () => setCursor((c) => ({ ...c, visible: false, press: false })))
  }

  // Dispara el tour cuando el mockup ya se ve bien en viewport (≥55%), una sola vez.
  useEffect(() => {
    if (reduced) return
    const el = rootRef.current
    if (!el) return
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || started.current || cancelled.current) return
        started.current = true
        io.disconnect()
        runDemo()
      },
      { threshold: 0.55 }
    )
    io.observe(el)
    return () => {
      io.disconnect()
      clearTimers()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduced])

  // Drawer mobile: la sidebar se oculta abajo de sm y se abre como overlay desde
  // el botón hamburguesa del topbar — igual que el shell real de la app.
  const [drawerOpen, setDrawerOpen] = useState(false)

  const onNav = (id: MainId) => {
    cancelled.current = true
    started.current = true
    clearTimers()
    setCursor((c) => ({ ...c, visible: false, press: false }))
    setScreen(id)
    setDrawerOpen(false)
  }

  return (
    // `dark`: el mockup muestra siempre el tema oscuro del software (mismo fondo y
    // colores que la app real), sin importar el tema de la landing.
    <div
      ref={rootRef}
      className="dark relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl shadow-primary/10"
    >
      {/* Barra del navegador */}
      <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-3">
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="ml-3 rounded-md bg-muted px-2.5 py-1 text-[11px] text-muted-foreground">
          app.wellnod.com
        </span>
      </div>

      {/* Shell: fondo verde + textura de la app + grano + paneles de glass */}
      <div className="relative flex h-[30rem] gap-3 bg-[radial-gradient(125%_125%_at_18%_12%,#d7e6df_0%,#aec7bb_50%,#85a394_100%)] p-3 dark:bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)]">
        {/* Misma textura de imagen que usa el fondo del software */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light"
          style={{ backgroundImage: "url('/app-bg-dark.png')" }}
        />
        {/* Grano/ruido sutil, igual que en la app */}
        <div
          aria-hidden
          className="bg-grain pointer-events-none absolute inset-0 opacity-[0.18] mix-blend-overlay"
        />
        {/* Backdrop del drawer (solo mobile, al abrir la sidebar desde el hamburguesa) */}
        {drawerOpen ? (
          <button
            type="button"
            aria-label="Menu"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 z-40 bg-black/40 sm:hidden"
          />
        ) : null}

        {/* Sidebar (navegable): estática en desktop, drawer overlay en mobile
            (mismo patrón que el shell real de la app). */}
        <aside
          className={cn(
            "z-50 w-52 flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl transition-transform duration-200 dark:border-white/10 dark:bg-black/30",
            "absolute inset-y-0 left-0 flex sm:static",
            drawerOpen ? "translate-x-0 shadow-2xl" : "-translate-x-[120%] sm:translate-x-0"
          )}
        >
          {/* Logo con la misma proporción que la sidebar real del software
              (hélix h-9 + título text-2xl, kerning pegado). */}
          <div className="flex h-14 shrink-0 items-center px-4">
            <span className="inline-flex items-center gap-2.5 text-foreground">
              <WellnodMark className="h-9 w-auto" />
              <span className="font-brand translate-y-0.5 text-2xl leading-none tracking-tight">
                <span className="font-bold">Well</span>
                <span className="-ml-[2px] font-light text-foreground/55">nod</span>
              </span>
            </span>
          </div>
          {/* La lista se corta abajo con un fundido: sugiere que hay más, pero no scrollea */}
          <nav className="min-h-0 flex-1 overflow-hidden [mask-image:linear-gradient(to_bottom,#000_calc(100%-2rem),transparent)]">
            <div className="flex flex-col gap-1 px-3 pb-3">
              {NAV_MAIN.map((it) => {
                const active = screen === it.id
                return (
                  <button
                    key={it.id}
                    ref={it.id === "advisor" ? asesorNavRef : undefined}
                    type="button"
                    onClick={() => onNav(it.id)}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "relative flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition-colors active:scale-[0.98]",
                      active
                        ? "bg-primary font-medium text-primary-foreground shadow-sm"
                        : "text-foreground/70 hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <it.icon className="size-[18px] shrink-0" />
                    {t.navMain[it.id]}
                  </button>
                )
              })}
              <p className="px-3 pt-3 pb-1 text-[10px] font-medium tracking-wider text-muted-foreground/50 uppercase">
                {t.opsLabel}
              </p>
              {NAV_OPS.map((it) => (
                <div
                  key={it.id}
                  className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-foreground/70"
                >
                  <it.icon className="size-[18px] shrink-0" />
                  {t.navOps[it.id]}
                </div>
              ))}
            </div>
          </nav>
          <div className="flex shrink-0 items-center gap-2.5 border-t border-black/10 p-3 dark:border-white/10">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              {t.ownerInitials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">{t.ownerName}</p>
              <p className="truncate text-xs text-muted-foreground">{t.ownerRole}</p>
            </div>
          </div>
        </aside>

        {/* Contenido */}
        <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl dark:border-white/10 dark:bg-black/30">
          {/* Topbar */}
          <header className="flex h-14 shrink-0 items-center gap-3 border-b border-black/10 px-5 dark:border-white/10">
            <button
              type="button"
              aria-label="Menu"
              onClick={() => setDrawerOpen(true)}
              className="-ml-1 grid size-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground sm:hidden"
            >
              <Menu className="size-4" />
            </button>
            <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
              {t.venue}
            </span>
            <div className="flex-1" />
            <span className="text-sm tabular-nums text-muted-foreground">{t.clock}</span>
            <span className="rounded-lg bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground">
              {t.onShift}
            </span>
          </header>

          {/* La pantalla cambia según la sidebar (fade al cambiar). Sin scroll: se ve la parte de arriba. */}
          <div key={screen} className="screen-fade min-h-0 flex-1 overflow-hidden p-5 text-left">
            {screen === "home" ? (
              <InicioScreen t={t} />
            ) : screen === "finance" ? (
              <FinanzasScreen t={t} />
            ) : screen === "customers" ? (
              <ClientesScreen t={t} />
            ) : screen === "products" ? (
              <ProductosScreen t={t} />
            ) : screen === "insights" ? (
              <CopilotScreen t={t} />
            ) : screen === "reports" ? (
              <ReportesScreen t={t} />
            ) : (
              <AsesorScreen t={t} buttonRef={tryCopilotRef} onTryCopilot={() => onNav("insights")} />
            )}
          </div>
        </div>
      </div>

      {/* Cursor del tour guiado: overlay que se mueve entre los botones y "clickea". */}
      {!reduced ? (
        <div
          aria-hidden
          className="pointer-events-none absolute left-0 top-0 z-30"
          style={{
            transform: `translate(${cursor.x}px, ${cursor.y}px)`,
            opacity: cursor.visible ? 1 : 0,
            transition: cursor.snap
              ? "opacity 0.25s ease"
              : "transform 0.7s cubic-bezier(0.22,1,0.36,1), opacity 0.25s ease",
          }}
        >
          <span className="relative block">
            <span
              className={cn(
                "absolute left-0 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary transition-all duration-300 ease-out",
                cursor.press ? "size-10 opacity-60" : "size-2 opacity-0"
              )}
            />
            <span
              className="block transition-transform duration-150"
              style={{ transform: cursor.press ? "scale(0.82)" : "scale(1)" }}
            >
              <CursorIcon />
            </span>
          </span>
        </div>
      ) : null}
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  )
}

// Cursor de puntero para el autoplay del demo (relleno blanco con borde oscuro).
function CursorIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 16 16"
      fill="none"
      className="drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)]"
    >
      <path
        d="M2 1.5 L2 12.5 L5 9.7 L7.1 14 L9 13.1 L6.9 8.9 L11 8.9 Z"
        fill="#ffffff"
        stroke="#0f172a"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function Pill({ children, tone }: { children: ReactNode; tone: Tone }) {
  const tones = {
    green: "bg-primary/12 text-primary",
    amber: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    red: "bg-destructive/12 text-destructive",
    muted: "bg-muted text-muted-foreground",
  }
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", tones[tone])}>
      {children}
    </span>
  )
}

function MiniTable({ cols, rows }: { cols: Col[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {cols.map((c) => (
              <th
                key={c.h}
                className={cn(
                  "px-3 py-2 text-xs font-medium text-muted-foreground",
                  c.right ? "text-right" : "text-left"
                )}
              >
                {c.h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri} className={ri > 0 ? "border-t border-border/60" : ""}>
              {r.map((cell, ci) => (
                <td
                  key={ci}
                  className={cn(
                    "px-3 py-2 text-foreground",
                    cols[ci]?.right ? "text-right tabular-nums" : ""
                  )}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ScreenHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="font-display text-xl font-bold text-foreground">{title}</h2>
        {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {right}
    </div>
  )
}

function RangeChips({ labels }: { labels: string[] }) {
  // El activo por defecto es "Mes"/"Month" (índice 2), como en la app real.
  return (
    <div className="flex gap-1">
      {labels.map((r, i) => (
        <span
          key={r}
          className={cn(
            "rounded-lg px-2.5 py-1 text-xs font-medium",
            i === 2
              ? "bg-primary text-primary-foreground"
              : "border border-border text-muted-foreground"
          )}
        >
          {r}
        </span>
      ))}
    </div>
  )
}

// ── Pantallas ───────────────────────────────────────────────────────────────
function InicioScreen({ t }: { t: Copy }) {
  const s = t.inicio
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-sm text-muted-foreground">{s.profitLabel}</p>
        <p className="text-3xl font-bold tabular-nums text-foreground sm:text-4xl">{s.profitValue}</p>
        <p className="mt-1 text-sm font-medium text-primary">{s.delta}</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {s.kpis.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-border p-4">
        <p className="text-sm font-semibold text-foreground">{s.channelsTitle}</p>
        <div className="mt-3 flex flex-col gap-2">
          {s.channels.map((r) => (
            <div key={r.m} className="flex items-center gap-3 text-xs">
              <span className="w-24 shrink-0 text-muted-foreground">{r.m}</span>
              <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <span className="block h-full rounded-full bg-primary" style={{ width: r.w }} />
              </span>
              <span className="w-8 shrink-0 text-right tabular-nums text-muted-foreground">
                {r.w}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FinanzasScreen({ t }: { t: Copy }) {
  const s = t.finanzas
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title={s.title} right={<RangeChips labels={t.ranges} />} />
      <div className="rounded-xl border border-border p-4">
        <p className="text-sm text-muted-foreground">{s.netLabel}</p>
        <p className="text-2xl font-bold tabular-nums text-foreground sm:text-3xl">{s.netValue}</p>
        <p className="mt-1 text-sm text-primary">{s.netDelta}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {s.cards.map((c) => (
          <div key={c.l} className="flex flex-col gap-1 rounded-xl border border-border p-4">
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className={cn("size-2 rounded-full", c.dot)} />
              {c.l}
            </span>
            <span className="text-lg font-bold tabular-nums text-foreground">{c.v}</span>
            <span className="text-xs text-muted-foreground">{c.act}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ClientesScreen({ t }: { t: Copy }) {
  const s = t.clientes
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader
        title={s.title}
        subtitle={s.subtitle}
        right={
          <span className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">
            {s.newBtn}
          </span>
        }
      />
      <MiniTable
        cols={s.cols}
        rows={s.rows.map((r) => [
          r.time,
          r.guest,
          r.party,
          r.service,
          r.table,
          <Pill tone={r.tone}>{r.status}</Pill>,
        ])}
      />
    </div>
  )
}

function ProductosScreen({ t }: { t: Copy }) {
  const s = t.productos
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title={s.title} subtitle={s.subtitle} right={<RangeChips labels={t.ranges} />} />
      <MiniTable
        cols={s.cols}
        rows={s.rows.map((p) => [
          p.name,
          p.price,
          p.keep,
          p.sold,
          <Pill tone={p.tone}>{p.status}</Pill>,
        ])}
      />
    </div>
  )
}

function ReportesScreen({ t }: { t: Copy }) {
  const s = t.reportes
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title={s.title} right={<RangeChips labels={t.ranges} />} />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {s.kpis.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-foreground">{s.mixTitle}</h3>
        <MiniTable
          cols={s.cols}
          rows={s.rows.map((r) => [r.method, r.type, r.ops, r.amount])}
        />
      </div>
    </div>
  )
}

function AsesorScreen({
  t,
  onTryCopilot,
  buttonRef,
}: {
  t: Copy
  onTryCopilot: () => void
  buttonRef?: Ref<HTMLButtonElement>
}) {
  const s = t.asesor
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader
        title={s.title}
        subtitle={s.subtitle}
        right={
          <div className="flex flex-wrap items-end gap-2">
            <span className="rounded-lg border border-border px-2.5 py-1.5 text-xs text-muted-foreground">
              {s.monthChip}
            </span>
            <span className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground">
              {s.configCosts}
            </span>
          </div>
        }
      />

      <button
        ref={buttonRef}
        type="button"
        onClick={onTryCopilot}
        className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-primary/10"
      >
        <Sparkles className="size-4 shrink-0 text-primary" />
        {s.bannerBefore}
        <b>{s.bannerCopilot}</b>
        {s.bannerAfter}
      </button>

      <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
        <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
        <p className="text-sm text-foreground">{s.summary}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {s.kpis.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function CopilotScreen({ t }: { t: Copy }) {
  const s = t.copilot
  const qa = s.qa
  const reduced = prefersReducedMotion()
  const [sel, setSel] = useState(0)
  const [answered, setAnswered] = useState(false)
  const [typed, setTyped] = useState(reduced ? qa[0].q : "")
  const typer = useRef<number | null>(null)

  const stopTyping = () => {
    if (typer.current !== null) {
      window.clearInterval(typer.current)
      typer.current = null
    }
  }

  // Al elegir una pregunta se "tipea" sola en el campo, letra por letra, para que se
  // entienda que ahí va la pregunta. Con reduced-motion aparece entera de una.
  useEffect(() => {
    const full = qa[sel].q
    stopTyping()
    if (reduced) {
      setTyped(full)
      return
    }
    setTyped("")
    let i = 0
    typer.current = window.setInterval(() => {
      i += 1
      setTyped(full.slice(0, i))
      if (i >= full.length) stopTyping()
    }, 38)
    return stopTyping
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel, reduced])

  // Si aprieta "Preguntar" mientras todavía se está tipeando, completa y responde.
  const ask = () => {
    stopTyping()
    setTyped(qa[sel].q)
    setAnswered(true)
  }

  const typing = typed.length < qa[sel].q.length

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="font-display text-xl font-bold text-foreground">{s.title}</h2>
        <p className="text-sm text-muted-foreground">{s.subtitle}</p>
      </div>

      <div className="flex gap-2">
        <div className="flex min-h-[2.375rem] min-w-0 flex-1 items-center truncate rounded-lg border border-border px-3 py-2 text-sm text-foreground">
          {typed}
          {typing ? (
            <span className="ml-px inline-block h-[1.1em] w-px shrink-0 animate-pulse bg-foreground" />
          ) : null}
        </div>
        <button
          type="button"
          onClick={ask}
          className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition active:scale-[0.97]"
        >
          {s.askBtn}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {qa.map((item, i) => (
          <button
            key={item.q}
            type="button"
            onClick={() => {
              setSel(i)
              setAnswered(false)
            }}
            className={cn(
              "rounded-lg border px-2.5 py-1 text-xs transition-colors active:scale-[0.98]",
              i === sel
                ? "border-primary bg-primary/10 text-foreground"
                : "border-border text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            {item.q}
          </button>
        ))}
      </div>

      {answered ? (
        <div
          key={sel}
          className="screen-fade flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4"
        >
          <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
          <p className="text-sm text-foreground">{qa[sel].a}</p>
        </div>
      ) : null}

      {/* Aclaración del demo: solo una vez que preguntó, junto con la respuesta. */}
      {answered ? (
        <p className="screen-fade rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
          {s.demoNote}
        </p>
      ) : null}
    </div>
  )
}
