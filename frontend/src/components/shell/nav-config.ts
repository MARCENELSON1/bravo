import type { ComponentType } from "react"
import {
  Boxes,
  CalendarClock,
  ChefHat,
  Clock,
  FileText,
  LayoutDashboard,
  Package,
  Plug,
  QrCode,
  Receipt,
  Truck,
  UtensilsCrossed,
  Users,
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

// Sidebar groups. Each item is gated by role (in addition to the route guards).
export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Resumen",
    items: [
      {
        label: "Dashboard",
        to: "/app",
        icon: LayoutDashboard,
        roles: ["OWNER", "MANAGER", "CASHIER"],
        end: true,
      },
    ],
  },
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
      {
        label: "Reservas",
        to: "/app/reservations",
        icon: CalendarClock,
        roles: ["WAITER", "CASHIER", "MANAGER", "OWNER"],
      },
      {
        label: "Fichar",
        to: "/app/fichar",
        icon: QrCode,
        roles: ["OWNER", "MANAGER", "WAITER", "KITCHEN", "CASHIER"],
      },
    ],
  },
  {
    label: "Catálogo",
    items: [
      { label: "Productos", to: "/app/products", icon: Package, roles: ["OWNER", "MANAGER"] },
    ],
  },
  {
    label: "Stock",
    items: [
      { label: "Insumos", to: "/app/stock", icon: Boxes, roles: ["OWNER", "MANAGER"] },
      { label: "Proveedores", to: "/app/suppliers", icon: Truck, roles: ["OWNER", "MANAGER"] },
    ],
  },
  {
    label: "Finanzas",
    items: [
      { label: "Egresos", to: "/app/expenses", icon: Receipt, roles: ["OWNER", "MANAGER"] },
      {
        label: "Comprobantes",
        to: "/app/invoices",
        icon: FileText,
        roles: ["OWNER", "MANAGER"],
      },
    ],
  },
  {
    label: "Administración",
    items: [
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
