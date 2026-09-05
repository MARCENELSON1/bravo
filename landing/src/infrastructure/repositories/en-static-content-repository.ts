import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

// Contenido de la landing para la región INTL (inglés, mercado US). NO es traducción
// literal del repo AR: es transcreación — ARCA → sales tax, MercadoPago → Stripe,
// MercadoPago → Stripe. Misma forma que StaticContentRepository.
const FEATURES: readonly Feature[] = [
  {
    id: "orders",
    icon: "orders",
    group: "operation",
    title: "Digital order taking",
    description:
      "Your server takes the order on a phone and it lands in the kitchen and bar on its own. No paper, no running back.",
  },
  {
    id: "kds",
    icon: "kds",
    group: "operation",
    title: "Kitchen & bar",
    description:
      "Each station sees its own tickets, sorted by time and status. Fewer mistakes, faster service.",
  },
  {
    id: "payments",
    icon: "payments",
    group: "operation",
    title: "Register, payments & tips",
    description:
      "Open and close the register with its count, take any payment method, and split the shift's tips.",
  },
  {
    id: "invoices",
    icon: "invoices",
    group: "management",
    title: "Sales tax & receipts",
    description:
      "Tax is calculated at checkout and the receipt goes out in the same step. No double data entry.",
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
      "Set a minimum per item, get told when something is running low, and keep your suppliers on hand.",
  },
  {
    id: "reservations",
    icon: "reservations",
    group: "management",
    title: "Reservations & guests",
    description:
      "The shift's book with confirmations and no-shows, plus your guest list to bring people back.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    group: "management",
    title: "Time tracking & staff",
    description:
      "Clock-ins and clock-outs from the restaurant, with everyone's hours ready for payroll.",
  },
  {
    id: "finance",
    icon: "finance",
    group: "management",
    title: "Finance & expenses",
    description:
      "Log what the restaurant spends and see what you collected net of fees. Money in and money out, together.",
  },
  {
    id: "reports",
    icon: "reports",
    group: "intelligence",
    title: "Reports & analytics",
    description:
      "Sales by day, payment method mix, and top sellers. Live, with no spreadsheets to build.",
  },
  {
    id: "copilot",
    icon: "copilot",
    group: "intelligence",
    title: "AI copilot",
    description:
      "Ask your business: “How much did I sell today?”, “Which dish has the best margin?”",
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
    description: "Menu, prices, tables, and team. In minutes, with no technical help.",
  },
  {
    id: "order",
    title: "Your server takes the order",
    description:
      "From a phone, at the table. It reaches the kitchen and bar on its own, sorted by time.",
  },
  {
    id: "charge",
    title: "You charge and file tax",
    description:
      "Payment, sales tax, and the register close with its count. All in one flow.",
  },
  {
    id: "copilot",
    title: "You ask the Copilot",
    description:
      "“How much did I sell today?”, “Which dish has the best margin?”. It answers with your real data.",
  },
  {
    id: "advisor",
    title: "The Advisor tells you what to do",
    description:
      "Net margin, prime cost, and break-even, with what to fix today and what to fix this week.",
  },
]

export class EnStaticContentRepository implements ContentRepository {
  async getFeatures(): Promise<readonly Feature[]> {
    return FEATURES
  }

  async getSteps(): Promise<readonly Step[]> {
    return STEPS
  }

}
