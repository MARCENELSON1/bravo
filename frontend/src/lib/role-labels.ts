import type { Role } from "@/api/types"

// Spanish labels for roles (UX is Spanish; the code/values stay English).
export const ROLE_LABELS: Record<Role, string> = {
  OWNER: "Dueño",
  MANAGER: "Encargado",
  WAITER: "Mozo",
  KITCHEN: "Cocina",
  BAR: "Barra",
  CASHIER: "Cajero",
}
