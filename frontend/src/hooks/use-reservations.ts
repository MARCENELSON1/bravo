import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type {
  CreateReservationBody,
  ReservationsQuery,
  UpdateReservationBody,
} from "@/api/types-reservations"
import { useServices } from "@/services/services-context"

export function useReservations(query: ReservationsQuery) {
  const { reservationsApi } = useServices()
  return useQuery({
    queryKey: ["reservations", query],
    queryFn: () => reservationsApi.list(query),
  })
}

export function useCreateReservation() {
  const { reservationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateReservationBody) => reservationsApi.create(body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["reservations"] }),
  })
}

export function useUpdateReservation() {
  const { reservationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateReservationBody }) =>
      reservationsApi.update(id, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["reservations"] }),
  })
}

// One mutation for the lifecycle transitions; the action selects the endpoint.
type TransitionAction = "confirm" | "seat" | "complete" | "cancel" | "noShow"

export function useReservationTransition() {
  const { reservationsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: TransitionAction }) =>
      reservationsApi[action](id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["reservations"] }),
  })
}
