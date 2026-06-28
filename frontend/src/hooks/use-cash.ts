import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { PaymentMethod } from "@/api/types-operations"
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
