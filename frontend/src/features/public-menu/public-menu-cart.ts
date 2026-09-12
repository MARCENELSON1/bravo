import type {
  CustomerOrderLineDTO,
  PublicMenuItemDTO,
  PublicMenuModifierGroupDTO,
} from "@/api/public-menu-api"

// Carrito de la carta QR (Carta QR F2 E). Un ítem con modificadores puede entrar
// varias veces con combos distintos → el carrito es una lista de líneas, no un
// mapa por producto. La `key` agrupa líneas idénticas (mismo producto + opciones).
export interface CartLine {
  key: string
  productId: string
  name: string
  unitPrice: number // base + suma de los deltas elegidos (minor units)
  quantity: number
  optionIds: string[]
  optionsLabel: string // "Con panceta · Extra queso" (vacío si no hay opciones)
}

// Clave estable de una línea: producto + opciones ordenadas (para agrupar iguales).
export function lineKey(productId: string, optionIds: string[]): string {
  return `${productId}|${[...optionIds].sort().join(",")}`
}

export function cartCount(lines: CartLine[]): number {
  return lines.reduce((n, line) => n + line.quantity, 0)
}

export function cartTotal(lines: CartLine[]): number {
  return lines.reduce((sum, line) => sum + line.unitPrice * line.quantity, 0)
}

export function toOrderLines(lines: CartLine[]): CustomerOrderLineDTO[] {
  return lines.map((line) => ({
    product_id: line.productId,
    quantity: line.quantity,
    ...(line.optionIds.length > 0 ? { option_ids: line.optionIds } : {}),
  }))
}

// Construye una línea a partir del ítem + las opciones elegidas. El precio se
// calcula acá para mostrar el total en vivo, pero el server SIEMPRE lo recalcula
// al enviar (el carrito solo manda ids) — nunca se confía el precio del cliente.
export function buildLine(item: PublicMenuItemDTO, optionIds: string[]): CartLine {
  const groups = item.modifier_groups ?? []
  const chosen = groups
    .flatMap((g) => g.options)
    .filter((o) => optionIds.includes(o.id))
  const delta = chosen.reduce((sum, o) => sum + o.price_delta, 0)
  return {
    key: lineKey(item.id, optionIds),
    productId: item.id,
    name: item.name,
    unitPrice: item.price_amount + delta,
    quantity: 1,
    optionIds: [...optionIds],
    optionsLabel: chosen.map((o) => o.name).join(" · "),
  }
}

// Una selección es válida cuando cada grupo respeta su min/max.
export function isSelectionValid(
  groups: PublicMenuModifierGroupDTO[],
  selectedIds: string[]
): boolean {
  return groups.every((group) => {
    const count = group.options.filter((o) => selectedIds.includes(o.id)).length
    return count >= group.min_select && count <= group.max_select
  })
}
