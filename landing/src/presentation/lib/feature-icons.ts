import {
  BarChart3,
  ChefHat,
  ClipboardList,
  Clock,
  CreditCard,
  Sparkles,
  type LucideIcon,
} from "lucide-react"

import type { FeatureIcon } from "@/domain/entities/feature"

// Traduce la clave semántica del dominio (string) a un componente de ícono.
// El dominio no conoce lucide; el mapeo vive en presentación (una sola fuente).
export const FEATURE_ICONS: Record<FeatureIcon, LucideIcon> = {
  orders: ClipboardList,
  payments: CreditCard,
  copilot: Sparkles,
  kds: ChefHat,
  timeclock: Clock,
  reports: BarChart3,
}
