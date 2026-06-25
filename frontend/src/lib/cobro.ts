import type { OrderItemDTO } from "@/api/types-operations"

// Quick amounts (minor units) the cashier can tap instead of typing: the full
// remaining, or splitting it among 2 or 3 people.
export function presetAmounts(remaining: number): { label: string; amount: number }[] {
  if (remaining <= 0) return []
  return [
    { label: "Total", amount: remaining },
    { label: "½", amount: Math.ceil(remaining / 2) },
    { label: "⅓", amount: Math.ceil(remaining / 3) },
  ]
}

// Sum (minor units) of the selected line items — used to split a bill by item.
export function sumLineItems(items: OrderItemDTO[], selectedIds: Set<string>): number {
  return items
    .filter((it) => selectedIds.has(it.id))
    .reduce((total, it) => total + it.unit_price_amount * it.quantity, 0)
}
