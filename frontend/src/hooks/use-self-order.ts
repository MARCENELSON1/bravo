import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { SelfOrderSettingsDTO } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

// Config del autopedido (Carta QR F2). Lado dueño.
export function useSelfOrderSettings() {
  const { selfOrderApi } = useServices()
  return useQuery({
    queryKey: ["self-order", "settings"],
    queryFn: () => selfOrderApi.settings(),
  })
}

export function useUpdateSelfOrderSettings() {
  const { selfOrderApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (settings: SelfOrderSettingsDTO) => selfOrderApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["self-order", "settings"], data)
    },
  })
}
