import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { FiscalAddressInput } from "@/api/types-tenant"
import { useServices } from "@/services/services-context"

export function useFiscalSettings() {
  const { tenantsApi } = useServices()
  return useQuery({
    queryKey: ["fiscal-settings"],
    queryFn: () => tenantsApi.fiscalSettings(),
  })
}

// El impuesto a sumar sobre una orden. Se re-consulta cuando cambia el total
// (la key incluye totalAmount). Deshabilitado si la orden está vacía.
export function useOrderTaxQuote(orderId: string, totalAmount: number) {
  const { ordersApi } = useServices()
  return useQuery({
    queryKey: ["order-tax-quote", orderId, totalAmount],
    queryFn: () => ordersApi.taxQuote(orderId),
    enabled: totalAmount > 0,
  })
}

export function useUpdateFiscalAddress() {
  const { tenantsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: FiscalAddressInput) => tenantsApi.updateFiscalAddress(body),
    onSuccess: (data) => {
      queryClient.setQueryData(["fiscal-settings"], data)
    },
  })
}
