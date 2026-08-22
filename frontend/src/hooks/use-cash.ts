import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type {
  CashMovementKind,
  CashSettingsDTO,
  PaymentMethod,
} from "@/api/types-operations"
import { useServices } from "@/services/services-context"

// The currently open register's live arqueo (null when none is open).
export function useCurrentCashSession() {
  const { cashApi } = useServices()
  return useQuery({
    queryKey: ["cash-session"],
    queryFn: () => cashApi.current(),
    refetchInterval: 15000, // keep the esperado fresh as cobros land
  })
}

export function useOpenCashSession() {
  const { cashApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { amount: number; note?: string | null }) =>
      cashApi.open(vars.amount, vars.note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}

interface CloseVars {
  sessionId: string
  counted: Partial<Record<PaymentMethod, number>>
  note?: string | null
}

export function useCloseCashSession() {
  const { cashApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: CloseVars) => cashApi.close(vars.sessionId, vars.counted, vars.note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}

// Propinas ganadas vs liquidadas por mozo. Sin ventana = histórico completo.
export function useTipsReport(from?: string, to?: string) {
  const { cashApi } = useServices()
  return useQuery({
    queryKey: ["tips-report", from ?? null, to ?? null],
    queryFn: () => cashApi.tipsReport(from, to),
  })
}

export function usePayTip() {
  const { cashApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { waiterId: string; amount: number }) =>
      cashApi.payTip(vars.waiterId, vars.amount),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["tips-report"] })
      void queryClient.invalidateQueries({ queryKey: ["expenses"] })
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}

export function useRegisterCashMovement() {
  const { cashApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { kind: CashMovementKind; amount: number; reason?: string | null }) =>
      cashApi.registerMovement(vars.kind, vars.amount, vars.reason),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}

export function useCashSettings() {
  const { cashApi } = useServices()
  return useQuery({ queryKey: ["cash-settings"], queryFn: () => cashApi.settings() })
}

export function useUpdateCashSettings() {
  const { cashApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (settings: CashSettingsDTO) => cashApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["cash-settings"], data)
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}
