import { useQuery } from "@tanstack/react-query"

import type { FinanceQuery } from "@/api/finance-api"
import { useServices } from "@/services/services-context"

// La Pantalla Finanzas en un request: KPIs vitales + comparativo + diagnósticos
// + margen por producto, para la ventana { from, to }.
export function useFinanceOverview(query: FinanceQuery) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-overview", query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.overview(query),
  })
}

// Drill-down de un producto. `enabled` para cargar solo cuando se expande la fila.
export function useProductDetail(productId: string | null, query: FinanceQuery) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-product", productId, query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.productDetail(productId as string, query),
    enabled: Boolean(productId),
  })
}
