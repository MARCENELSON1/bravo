import { useMutation, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

// Mark that a table asked for the bill (→ "a cobrar" on the floor). Invalidates
// the floor so the state flips immediately (the SSE poll would catch it too).
export function useRequestBill() {
  const { floorApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => floorApi.requestBill(sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["floor"] }),
  })
}

// Correct how many people are seated on a table's open session.
export function useSetPax() {
  const { floorApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { sessionId: string; pax: number }) =>
      floorApi.setPax(vars.sessionId, vars.pax),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["floor"] }),
  })
}
