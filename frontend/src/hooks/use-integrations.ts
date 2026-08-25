import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AfipConnectBody } from "@/api/types-invoicing"
import type { TaxJarConnectBody } from "@/api/types-tenant"
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

export function useTaxJarConnection(enabled = true) {
  const { integrationsApi } = useServices()
  return useQuery({
    queryKey: ["taxjar-connection"],
    queryFn: () => integrationsApi.getTaxJarStatus(),
    enabled, // AR (motor NONE) no consulta la integración US
  })
}

export function useConnectTaxJar() {
  const { integrationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TaxJarConnectBody) => integrationsApi.connectTaxJar(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["taxjar-connection"] })
    },
  })
}

export function useDisconnectTaxJar() {
  const { integrationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => integrationsApi.disconnectTaxJar(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["taxjar-connection"] })
    },
  })
}
