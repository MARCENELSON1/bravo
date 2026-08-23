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
