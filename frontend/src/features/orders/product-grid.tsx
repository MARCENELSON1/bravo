import { useMemo, useState } from "react"

import type { ProductDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { formatMoney } from "@/lib/money"
import { getUsage, rankProducts } from "@/lib/product-usage"

// Fast product picker: search-as-you-type + a tappable grid (most-used first),
// with a quantity stepper. Tapping a card adds it instantly (optimistic), so a
// comanda is a few taps instead of scrolling a dropdown.
export function ProductGrid({
  products,
  onAdd,
}: {
  products: ProductDTO[]
  onAdd: (product: ProductDTO, quantity: number) => void
}) {
  const [search, setSearch] = useState("")
  const [qty, setQty] = useState(1)
  const ranked = useMemo(() => rankProducts(products, search, getUsage()), [products, search])

  const add = (product: ProductDTO) => {
    onAdd(product, qty)
    setQty(1) // reset to the common case after each add
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Input
          placeholder="Buscar producto…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            className="h-9 w-9 p-0 text-lg"
            onClick={() => setQty((q) => Math.max(1, q - 1))}
            aria-label="Menos cantidad"
          >
            −
          </Button>
          <span className="w-7 text-center text-sm font-medium tabular-nums">{qty}</span>
          <Button
            variant="outline"
            className="h-9 w-9 p-0 text-lg"
            onClick={() => setQty((q) => q + 1)}
            aria-label="Más cantidad"
          >
            +
          </Button>
        </div>
      </div>

      {ranked.length > 0 ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {ranked.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => add(p)}
              className="flex min-h-16 flex-col items-start justify-between gap-1 rounded-lg border bg-card p-3 text-left transition hover:border-primary hover:bg-accent active:scale-[0.98]"
            >
              <span className="text-sm font-medium leading-tight">{p.name}</span>
              <span className="text-xs text-muted-foreground">
                {formatMoney(p.price_amount, p.currency)}
              </span>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Sin productos que coincidan.</p>
      )}
    </div>
  )
}
