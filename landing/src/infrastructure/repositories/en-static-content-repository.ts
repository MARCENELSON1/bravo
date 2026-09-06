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

const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Set up your restaurant once",
    description:
      "Tables and sections, the menu with its recipes and costs, and your team with each person's role. In minutes and with no technical help.",
  },
  {
    id: "order",
    title: "Open the table and take the order",
    description:
      "From a phone, out on the floor. The kitchen and bar get their part right away and flag when the plate is up.",
  },
  {
    id: "charge",
    title: "Charge, file tax, and close out",
    description:
      "Any payment method, tax filed in the same step, tips shared out, and a count at close. Stock draws down from the recipe.",
  },
  {
    id: "copilot",
    title: "You ask the Copilot",
    description:
      "“How much did I sell today?”, “Which dish has the best margin?”. It answers with your data and shows where every number came from.",
  },
  {
    id: "advisor",
    title: "The Advisor tells you what to do",
    description:
      "With your costs in: net margin, prime cost, and break-even, plus what is worth doing today and this week.",
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
