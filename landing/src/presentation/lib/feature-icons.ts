import {
  Boxes,
  CalendarCheck,
  ChefHat,
  Clock,
  CreditCard,
  Lightbulb,
  LineChart,
  Package,
  ScrollText,
  Sparkles,
  UtensilsCrossed,
  Wallet,
  type LucideIcon,
} from "lucide-react"

import type { FeatureIcon } from "@/domain/entities/feature"

// Traduce la clave semántica del dominio (string) a un componente de ícono.
// El dominio no conoce lucide; el mapeo vive en presentación (una sola fuente).
// Se usan los MISMOS íconos que la sidebar del software, para que quien entra
// después de ver la landing reconozca cada área.
export const FEATURE_ICONS: Record<FeatureIcon, LucideIcon> = {
  orders: UtensilsCrossed,
  kds: ChefHat,
  payments: CreditCard,
  invoices: ScrollText,
  menu: Package,
  inventory: Boxes,
  reservations: CalendarCheck,
  timeclock: Clock,
  finance: Wallet,
  reports: LineChart,
  copilot: Lightbulb,
  advisor: Sparkles,
}
