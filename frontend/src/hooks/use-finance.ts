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

// Egresos por categoría (donut + "3 gastos que más cambiaron").
export function useExpenseBreakdown(query: FinanceQuery) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-expense-breakdown", query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.expenseBreakdown(query),
  })
}

// Últimos movimientos (solo se usa en modo Hoy/Semana).
export function useRecentMovements(query: FinanceQuery, enabled: boolean) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-movements", query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.recentMovements(query),
    enabled,
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
