import type { ComponentType } from "react"
import { FileText, Home, Lightbulb, LineChart, Package, Users } from "lucide-react"

import type { Role } from "@/api/types"

export interface NavItem {
  label: string
  to: string
  icon: ComponentType<{ className?: string }>
  roles: Role[]
  end?: boolean
}

// Flat sidebar nav (Wellnod dashboard IA). Each item is gated by role in addition
// to the route guards. Labels are the customer-facing ES names; routes reuse the
// existing feature pages.
export const NAV_ITEMS: NavItem[] = [
  {
    label: "Inicio",
    to: "/app",
    icon: Home,
    roles: ["OWNER", "MANAGER", "CASHIER", "WAITER", "KITCHEN"],
    end: true,
  },
  { label: "Finanzas", to: "/app/expenses", icon: LineChart, roles: ["OWNER", "MANAGER"] },
  {
    label: "Clientes",
    to: "/app/reservations",
    icon: Users,
    roles: ["OWNER", "MANAGER", "CASHIER", "WAITER"],
  },
  { label: "Productos", to: "/app/products", icon: Package, roles: ["OWNER", "MANAGER"] },
  { label: "IA Insights", to: "/app/copilot", icon: Lightbulb, roles: ["OWNER", "MANAGER"] },
  { label: "Reportes", to: "/app/analytics", icon: FileText, roles: ["OWNER", "MANAGER"] },
]
