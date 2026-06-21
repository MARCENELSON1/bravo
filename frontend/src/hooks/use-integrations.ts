import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useMpConnection() {
  const { integrationsApi } = useServices()
  return useQuery({
    queryKey: ["mp-connection"],
    queryFn: () => integrationsApi.getMpStatus(),
  })
}

export function useDisconnectMp() {
  const { integrationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => integrationsApi.disconnectMp(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mp-connection"] })
    },
  })
}
