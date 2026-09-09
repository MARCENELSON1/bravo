import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

// Contenido de la landing para la región INTL (inglés, mercado US). NO es traducción
// literal del repo AR: es transcreación — ARCA → sales tax, MercadoPago → Stripe.
// Misma forma y mismo orden que StaticContentRepository.
const FEATURES: readonly Feature[] = [
  {
    id: "floor",
    icon: "floor",
    group: "operation",
    title: "Floor & tables",
    description:
      "The live floor plan: which table is free, which is in the kitchen, which has food up to run, and which asked for the check. Tap one to open its order.",
  },
  {
    id: "orders",
    icon: "orders",
    group: "operation",
    title: "Digital order taking",
    description:
      "Your server takes the order on a phone, at the table, and it lands in the kitchen and bar on its own. No paper, no running back.",
  },
  {
    id: "kds",
    icon: "kds",
    group: "operation",
    title: "Kitchen & bar",
    description:
      "Each station sees its own tickets, sorted by time and status, and marks them off. Fewer mistakes, faster service.",
  },
  {
    id: "payments",
    icon: "payments",
    group: "operation",
    title: "Register, payments & tips",
    description:
      "Take any payment method, split the check by item, and share out the shift's tips. The register opens with its float and closes with a count.",
  },
  {
    id: "invoices",
    icon: "invoices",
    group: "operation",
    title: "Sales tax & receipts",
    description:
      "Tax is calculated at checkout and the receipt goes out in the same step. No double data entry.",
  },
  {
    id: "reservations",
    icon: "reservations",
    group: "operation",
    title: "Reservations",
    description:
      "The day's book by service: confirm, seat at a table, and log the no-shows.",
  },
  {
    id: "menu",
    icon: "menu",
    group: "management",
    title: "Menu & recipes",
    description:
      "Add products, prices, and recipes. Wellnod works out what each dish costs and the margin it leaves.",
  },
  {
    id: "inventory",
    icon: "inventory",
    group: "management",
    title: "Inventory & suppliers",
    description:
      "Set a minimum per item and get told when something is running low. Selling draws stock down from the recipe.",
  },
  {
    id: "crm",
    icon: "crm",
    group: "management",
    title: "Guests",
    description:
      "Your guest list with each one's visits, so you can message them on WhatsApp and bring them back.",
  },
  {
    id: "team",
    icon: "team",
    group: "management",
    title: "Team & permissions",
    description:
      "Invite your people by email and each one signs in with their role — owner, manager, server, kitchen, bar, register — and sees only their part.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    group: "management",
    title: "Time tracking & staff",
    description:
      "They clock in on site with a QR or a code. For each one: hours and overtime for payroll, tables served, and how much they sold.",
  },
  {
    id: "finance",
    icon: "finance",
    group: "management",
    title: "Finance & expenses",
    description:
      "Log what the restaurant spends and see what you collected net of fees. The period exports ready for your accountant.",
  },
  {
    id: "reports",
    icon: "reports",
    group: "intelligence",
    title: "Reports & analytics",
    description:
      "Sales by day, payment method mix, spend by category, and top sellers. Live, with no spreadsheets to build.",
  },
  {
    id: "copilot",
    icon: "copilot",
    group: "intelligence",
    title: "AI copilot",
    // OJO: "y actúa sobre lo que le pidas" todavía NO está implementado — el
    // copiloto es de solo lectura (backend: allow-list read-only, único endpoint
    // /copilot/ask). Se agregó a pedido, con la función prevista para más adelante.
    description:
      "“How much did I sell today?”, “Which dish has the best margin?”. It answers in plain language and acts on what you ask.",
  },
  {
    id: "advisor",
    icon: "advisor",
    group: "intelligence",
    title: "Advisor",
    description:
      "Net margin, prime cost, and break-even, with a read on what to do today and what to do this week.",
  },
]

// El recorrido completo, encadenado: cada paso usa lo que dejó el anterior.
//
// OJO: dos cosas de este texto NO están implementadas todavía — que el Copiloto
// ACCIONE (hoy es de solo lectura), la CARTA PARA EL CLIENTE con sus recomendaciones
// y la MIGRACIÓN desde otro sistema. Ver la nota larga en
// static-content-repository.ts.
const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Up and running in minutes, not weeks",
    description:
      "Everything the restaurant needs gets loaded once: tables, menu with each dish's cost, suppliers, and so on. And if you're coming from another system, you bring over what you already had. Nothing to install: that setup is the base, everything that follows feeds off it.",
  },
  {
    id: "order",
    title: "One menu, two screens",
    description:
      "Your server takes the order on the handheld, or your guests choose what they want from that same menu, with recommendations and the detail of every dish. Either way the order fires the same: each item lands in its station, kitchen or bar, and the table flags when it's ready to run.",
  },
  {
    id: "charge",
    title: "The sale closes the loop",
    description:
      "Take any payment and split by item when you need to. You can file the tax in the same step or leave it for later. Stock draws down from the recipe and the register is ready for the count at close.",
  },
  {
    id: "copilot",
    title: "The Copilot answers — and acts",
    description:
      "Every piece of data the floor produces turns into an answer: “how much did I sell this month?”, “which dish sold the most?”. It answers, shows you where the information comes from, and suggests what to do with it. And if you want, it makes the change itself.",
  },
  {
    id: "advisor",
    title: "The Advisor tells you where the money is",
    description:
      "It reads those same numbers —net margin, food cost, prime cost, break-even— and turns them into a short list: what to fix today, what to watch this week, and what's coming. With the data in front of you, so the call is yours.",
  },
]

// Adapter estático del puerto ContentRepository para INTL.
export class EnStaticContentRepository implements ContentRepository {
  getFeatures(): readonly Feature[] {
    return FEATURES
  }

  getSteps(): readonly Step[] {
    return STEPS
  }

}
