import type { Course, OrderDTO, OrderItemDTO } from "@/api/types-operations"

// Tiempos de servicio (coursing). El curso es del PLATO: se define una vez en la
// carta y se copia a cada línea, así el mozo no clasifica nada. La cocina cocina
// un curso a la vez y el mozo dispara el siguiente ("Marchar principal").
//
// Espeja `mobile/lib/features/order/order_dtos.dart` (`courseState`,
// `readyCourse`) para que las dos apps deriven lo mismo del mismo payload.

// Orden de servicio: las bebidas salen ya, después entrada → principal → postre.
export const COURSE_ORDER: readonly Course[] = [
  "IMMEDIATE",
  "STARTER",
  "MAIN",
  "DESSERT",
] as const

/** Curso de una línea. `MAIN` es el default del backend (y de las líneas viejas). */
export function courseOf(item: OrderItemDTO): Course {
  return item.course ?? "MAIN"
}

/** Estado derivado de un curso dentro de la comanda (nunca se almacena). */
export type CourseState = "PENDING" | "HELD" | "IN_KITCHEN" | "READY" | "SERVED"

/** Ítems que todavía cuentan (todo menos los anulados). */
export function liveItems(items: OrderItemDTO[]): OrderItemDTO[] {
  return items.filter((it) => it.status !== "CANCELLED")
}

export function itemsOfCourse(items: OrderItemDTO[], course: Course): OrderItemDTO[] {
  return liveItems(items).filter((it) => courseOf(it) === course)
}

/** Cursos presentes en la comanda, en orden de servicio. */
export function coursesOf(items: OrderItemDTO[]): Course[] {
  const present = new Set(liveItems(items).map(courseOf))
  return COURSE_ORDER.filter((c) => present.has(c))
}

/**
 * Precedencia: cocinando > hay platos listos > en espera > sin marchar >
 * servido. `null` = ese curso no tiene platos.
 */
export function courseState(items: OrderItemDTO[], course: Course): CourseState | null {
  const statuses = new Set(itemsOfCourse(items, course).map((it) => it.status))
  if (statuses.size === 0) return null
  if (statuses.has("SENT") || statuses.has("PREPARING")) return "IN_KITCHEN"
  if (statuses.has("READY")) return "READY"
  if (statuses.has("HELD")) return "HELD"
  if (statuses.has("PENDING")) return "PENDING"
  return "SERVED"
}

/**
 * Curso más bajo que está LISTO para servir: es lo que hay que llevar ahora.
 * Servir "toda la orden" mezclaría tiempos (la entrada lista con el principal
 * que recién sale), así que servir siempre va por curso.
 */
export function readyCourse(order: OrderDTO): Course | null {
  return COURSE_ORDER.find((c) => courseState(order.items, c) === "READY") ?? null
}

/** Platos cargados sin marchar (los que manda "Marchar"). */
export function pendingCount(order: OrderDTO): number {
  return order.items.filter((it) => it.status === "PENDING").length
}

/** Platos marchados esperando que el mozo dispare su curso. */
export function heldCount(order: OrderDTO): number {
  return order.items.filter((it) => it.status === "HELD").length
}

/** Próximo curso en espera; cae al derivado del server si vino. */
export function nextHeldCourse(order: OrderDTO): Course | null {
  if (order.next_course) return order.next_course
  return COURSE_ORDER.find((c) => courseState(order.items, c) === "HELD") ?? null
}
