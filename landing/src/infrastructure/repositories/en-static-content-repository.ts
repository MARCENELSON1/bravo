import type { Faq } from "@/domain/entities/faq"
import type { Feature } from "@/domain/entities/feature"
import type { Integration } from "@/domain/entities/integration"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

// Contenido de la landing para la región INTL (inglés, mercado US). NO es traducción
// literal del repo AR: es transcreación — AFIP → sales tax, MercadoPago → Stripe,
// copiloto en español → copilot in English. Misma forma que StaticContentRepository.
const FEATURES: readonly Feature[] = [
  {
    id: "orders",
    icon: "orders",
    title: "Digital order taking",
    description:
      "Your server takes the order from their phone and it lands straight in the kitchen and bar. No paper tickets, no back-and-forth.",
  },
  {
    id: "payments",
    icon: "payments",
    title: "Payments & automated sales tax",
    description:
      "Take card payments and let sales tax calculate itself on every check. No spreadsheets, no month-end scramble.",
  },
  {
    id: "copilot",
    icon: "copilot",
    title: "AI copilot in English",
    description:
      "Ask your business in plain English: “How much did I sell today?”, “Which dish has the best margin?”",
  },
  {
    id: "kds",
    icon: "kds",
    title: "Kitchen display (KDS)",
    description:
      "The kitchen sees orders sorted by time and status. Fewer mistakes, faster tickets.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    title: "Employee time tracking",
    description:
      "Clock staff in and out from the floor, with hours reports ready for payroll.",
  },
  {
    id: "reports",
    icon: "reports",
    title: "Real-time reporting",
    description:
      "Sales, cash, and margins at a glance. Decide with data, not gut feel.",
  },
]

const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Add your menu and tables",
    description:
      "Set up items, prices, and your floor once. In minutes, no tech help needed.",
  },
  {
    id: "order",
    title: "Your server takes the order",
    description: "From their phone, right at the table. No paper tickets, no shouting to the kitchen.",
  },
  {
    id: "kitchen",
    title: "Kitchen and bar get it instantly",
    description: "The order shows up on the KDS sorted by time. It's prepped and out faster.",
  },
  {
    id: "charge",
    title: "Charge, tax, and measure",
    description:
      "Card payment, sales tax on the same check, and today's report already updated.",
  },
]

const INTEGRATIONS: readonly Integration[] = [
  { id: "stripe", name: "Stripe", description: "Payments & cards" },
  { id: "salestax", name: "Sales tax", description: "Automatic filing" },
  { id: "printers", name: "Printers", description: "Tickets & receipts" },
  { id: "whatsapp", name: "WhatsApp", description: "Alerts & orders" },
  { id: "readers", name: "Card readers", description: "In-person payments" },
  { id: "sheets", name: "Export to Excel", description: "Reports & data" },
]

const FAQS: readonly Faq[] = [
  {
    id: "hardware",
    question: "Do I need to buy special hardware?",
    answer:
      "No. Wellnod runs on the phones, tablets, and computers you already have. If you want, it connects to kitchen ticket printers.",
  },
  {
    id: "tax",
    question: "Does it handle sales tax?",
    answer:
      "Yes. Sales tax is built in: you charge and the tax is calculated and filed for you, with no double entry.",
  },
  {
    id: "trial",
    question: "Is there a free trial?",
    answer:
      "Yes — every plan starts with a 30-day free trial. We ask for a card upfront and only charge when the trial ends. Cancel anytime before then and you won't be charged.",
  },
  {
    id: "multi",
    question: "Does it work if I have more than one location?",
    answer:
      "Yes. The Multi-location plan gives you one consolidated dashboard across all your locations, with roles and permissions per location.",
  },
  {
    id: "copilot",
    question: "What is the AI copilot?",
    answer:
      "It's an assistant that answers questions about your business in plain English — sales, margins, stock, and more — without you building reports.",
  },
  {
    id: "data",
    question: "Is my data safe?",
    answer:
      "Every location works with its own isolated data. Information is protected with encryption and security best practices.",
  },
]

export class EnStaticContentRepository implements ContentRepository {
  async getFeatures(): Promise<readonly Feature[]> {
    return FEATURES
  }

  async getSteps(): Promise<readonly Step[]> {
    return STEPS
  }

  async getIntegrations(): Promise<readonly Integration[]> {
    return INTEGRATIONS
  }

  async getFaqs(): Promise<readonly Faq[]> {
    return FAQS
  }
}
