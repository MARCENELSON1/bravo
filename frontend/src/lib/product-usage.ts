import type { ProductDTO } from "@/api/types-operations"

// Tracks how often each product is added (in localStorage) so the most-used
// products float to the top of the grid — "favoritos" that learn on their own,
// no backend needed. One device = one local; good enough for the MVP.
const KEY = "nucleo:product-usage"

export type UsageMap = Record<string, number>

function read(): UsageMap {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as UsageMap) : {}
  } catch {
    return {}
  }
}

export function getUsage(): UsageMap {
  return read()
}

export function bumpUsage(productId: string): void {
  try {
    const usage = read()
    usage[productId] = (usage[productId] ?? 0) + 1
    localStorage.setItem(KEY, JSON.stringify(usage))
  } catch {
    // localStorage unavailable (private mode) — ranking falls back to name only.
  }
}

// Pure: active products matching the search, most-used first, then alphabetical.
export function rankProducts(
  products: ProductDTO[],
  search: string,
  usage: UsageMap
): ProductDTO[] {
  const q = search.trim().toLowerCase()
  const matched = products.filter(
    (p) =>
      p.active &&
      (q === "" ||
        p.name.toLowerCase().includes(q) ||
        (p.category ?? "").toLowerCase().includes(q))
  )
  return matched.sort((a, b) => {
    const used = (usage[b.id] ?? 0) - (usage[a.id] ?? 0)
    return used !== 0 ? used : a.name.localeCompare(b.name)
  })
}
