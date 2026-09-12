import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { SelfPaySettingsDTO } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

// Config del pago desde la mesa (Carta QR F3). Lado dueño.
export function useSelfPaySettings() {
  const { selfPayApi } = useServices()
  return useQuery({
    queryKey: ["self-pay", "settings"],
    queryFn: () => selfPayApi.settings(),
  })
}

export function useUpdateSelfPaySettings() {
  const { selfPayApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (settings: SelfPaySettingsDTO) => selfPayApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["self-pay", "settings"], data)
    },
  })
}
