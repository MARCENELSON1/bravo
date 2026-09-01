import type { ComponentType } from "react"
import {
  Boxes,
  Calculator,
  CalendarCheck,
  ChefHat,
  Clock,
  Coffee,
  Coins,
  CreditCard,
  FileText,
  Home,
  Lightbulb,
  LineChart,
  Package,
  QrCode,
  Receipt,
  ScanLine,
  Sparkles,
  Truck,
  Users,
  UtensilsCrossed,
} from "lucide-react"

import type { Role } from "@/api/types"

export interface NavItem {
  label: string
  to: string
  icon: ComponentType<{ className?: string }>
  roles: Role[]
  end?: boolean
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

// Nav híbrida (identidad Wellnod): los destinos principales planos arriba +
// grupos "Operación" y "Gestión" debajo. Cada ítem sigue gateado por rol
// (además de los route guards) — misma cobertura de rutas que la nav previa.
export const NAV_ITEMS: NavItem[] = [
  {
    label: "shell.nav.home",
    to: "/app",
    icon: Home,
    roles: ["OWNER", "MANAGER", "WAITER", "KITCHEN", "BAR", "CASHIER"],
    end: true,
  },
  { label: "shell.nav.finance", to: "/app/finanzas", icon: LineChart, roles: ["OWNER", "MANAGER"] },
  {
    label: "shell.nav.customers",
    to: "/app/clientes",
    icon: Users,
    roles: ["OWNER", "MANAGER", "WAITER", "CASHIER"],
  },
  {
    label: "shell.nav.reservations",
    to: "/app/reservations",
    icon: CalendarCheck,
    roles: ["OWNER", "MANAGER", "WAITER", "CASHIER"],
  },
  { label: "shell.nav.products", to: "/app/products", icon: Package, roles: ["OWNER", "MANAGER"] },
  { label: "shell.nav.aiInsights", to: "/app/copilot", icon: Lightbulb, roles: ["OWNER", "MANAGER"] },
  { label: "shell.nav.advisor", to: "/app/advisor", icon: Sparkles, roles: ["OWNER", "MANAGER"] },
  { label: "shell.nav.analytics", to: "/app/analytics", icon: LineChart, roles: ["OWNER", "MANAGER"] },
  { label: "shell.nav.reports", to: "/app/reportes", icon: FileText, roles: ["OWNER", "MANAGER"] },
]

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "shell.groups.operation",
    items: [
      {
        label: "shell.nav.tables",
        to: "/app/floor",
        icon: UtensilsCrossed,
        roles: ["WAITER", "CASHIER", "MANAGER", "OWNER"],
      },
      { label: "shell.nav.kitchen", to: "/app/kds", icon: ChefHat, roles: ["KITCHEN", "MANAGER", "OWNER"] },
      { label: "shell.nav.bar", to: "/app/bar", icon: Coffee, roles: ["BAR", "MANAGER", "OWNER"] },
      {
        label: "shell.nav.cash",
        to: "/app/caja",
        icon: Calculator,
        roles: ["CASHIER", "MANAGER", "OWNER"],
      },
      {
        label: "shell.nav.tips",
        to: "/app/propinas",
        icon: Coins,
        roles: ["CASHIER", "MANAGER", "OWNER"],
      },
      {
        label: "shell.nav.clock",
        to: "/app/fichar",
        icon: QrCode,
        roles: ["OWNER", "MANAGER", "WAITER", "KITCHEN", "BAR", "CASHIER"],
      },
    ],
  },
  {
    label: "shell.groups.management",
    items: [
      { label: "shell.nav.expenses", to: "/app/expenses", icon: Receipt, roles: ["OWNER", "MANAGER"] },
      {
        label: "shell.nav.invoices",
        to: "/app/invoices",
        icon: FileText,
        roles: ["OWNER", "MANAGER"],
      },
      { label: "shell.nav.supplies", to: "/app/stock", icon: Boxes, roles: ["OWNER", "MANAGER"] },
      { label: "shell.nav.suppliers", to: "/app/suppliers", icon: Truck, roles: ["OWNER", "MANAGER"] },
      { label: "shell.nav.staff", to: "/app/staff", icon: Clock, roles: ["OWNER", "MANAGER"] },
      {
        label: "shell.nav.tableQr",
        to: "/app/mesas-qr",
        icon: ScanLine,
        roles: ["OWNER", "MANAGER"],
      },
      { label: "shell.nav.subscription", to: "/app/subscription", icon: CreditCard, roles: ["OWNER"] },
    ],
  },
]
