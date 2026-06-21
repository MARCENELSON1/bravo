import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AfipConnectBody } from "@/api/types-invoicing"
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

export function useAfipConnection() {
  const { integrationsApi } = useServices()
  return useQuery({
    queryKey: ["afip-connection"],
    queryFn: () => integrationsApi.getAfipStatus(),
  })
}

export function useConnectAfip() {
  const { integrationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: AfipConnectBody) => integrationsApi.connectAfip(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["afip-connection"] })
    },
  })
}

export function useDisconnectAfip() {
  const { integrationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => integrationsApi.disconnectAfip(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["afip-connection"] })
    },
  })
}
