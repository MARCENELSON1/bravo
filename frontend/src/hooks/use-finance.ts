import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

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

// Sales tax cobrado en la ventana (lo que se le debe al fisco; 0 en AR).
export function useTaxCollected(query: FinanceQuery = {}) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-tax-collected", query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.taxCollected(query),
  })
}

// Estado del outbox de reportes al fisco (por reportar / fallidas / reportadas).
export function useTaxReportStatus() {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-tax-report-status"],
    queryFn: () => financeApi.taxReportStatus(),
  })
}

// "Reportar ahora": dispara el drain y refresca el estado + el tax cobrado.
export function useReportPendingTax() {
  const { financeApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => financeApi.reportPendingTax(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["finance-tax-report-status"] })
    },
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
