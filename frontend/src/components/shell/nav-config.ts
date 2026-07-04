import type { ComponentType } from "react"
import {
  Boxes,
  Calculator,
  ChefHat,
  Clock,
  Coffee,
  Coins,
  FileText,
  Home,
  Lightbulb,
  LineChart,
  Package,
  Plug,
  QrCode,
  Receipt,
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
    label: "Inicio",
    to: "/app",
    icon: Home,
    roles: ["OWNER", "MANAGER", "WAITER", "KITCHEN", "BAR", "CASHIER"],
    end: true,
  },
  { label: "Finanzas", to: "/app/finanzas", icon: LineChart, roles: ["OWNER", "MANAGER"] },
  {
    label: "Clientes",
    to: "/app/reservations",
    icon: Users,
    roles: ["OWNER", "MANAGER", "WAITER", "CASHIER"],
  },
  { label: "Productos", to: "/app/products", icon: Package, roles: ["OWNER", "MANAGER"] },
  { label: "IA Insights", to: "/app/copilot", icon: Lightbulb, roles: ["OWNER", "MANAGER"] },
  { label: "Reportes", to: "/app/analytics", icon: FileText, roles: ["OWNER", "MANAGER"] },
]

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Operación",
    items: [
      {
        label: "Mesas",
        to: "/app/floor",
        icon: UtensilsCrossed,
        roles: ["WAITER", "CASHIER", "MANAGER", "OWNER"],
      },
      { label: "Cocina", to: "/app/kds", icon: ChefHat, roles: ["KITCHEN", "MANAGER", "OWNER"] },
      { label: "Barra", to: "/app/bar", icon: Coffee, roles: ["BAR", "MANAGER", "OWNER"] },
      {
        label: "Caja",
        to: "/app/caja",
        icon: Calculator,
        roles: ["CASHIER", "MANAGER", "OWNER"],
      },
      {
        label: "Propinas",
        to: "/app/propinas",
        icon: Coins,
        roles: ["CASHIER", "MANAGER", "OWNER"],
      },
      {
        label: "Fichar",
        to: "/app/fichar",
        icon: QrCode,
        roles: ["OWNER", "MANAGER", "WAITER", "KITCHEN", "BAR", "CASHIER"],
      },
    ],
  },
  {
    label: "Gestión",
    items: [
      { label: "Asesor", to: "/app/advisor", icon: Sparkles, roles: ["OWNER", "MANAGER"] },
      { label: "Egresos", to: "/app/expenses", icon: Receipt, roles: ["OWNER", "MANAGER"] },
      {
        label: "Comprobantes",
        to: "/app/invoices",
        icon: FileText,
        roles: ["OWNER", "MANAGER"],
      },
      { label: "Insumos", to: "/app/stock", icon: Boxes, roles: ["OWNER", "MANAGER"] },
      { label: "Proveedores", to: "/app/suppliers", icon: Truck, roles: ["OWNER", "MANAGER"] },
      { label: "Personal", to: "/app/staff", icon: Clock, roles: ["OWNER", "MANAGER"] },
      {
        label: "Integraciones",
        to: "/app/integrations",
        icon: Plug,
        roles: ["OWNER", "MANAGER"],
      },
      { label: "Equipo", to: "/app/invite", icon: Users, roles: ["OWNER", "MANAGER"] },
    ],
  },
]
