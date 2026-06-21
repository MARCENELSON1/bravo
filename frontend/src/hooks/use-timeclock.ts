import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AdjustShiftBody, ShiftsQuery } from "@/api/types-timeclock"
import { useServices } from "@/services/services-context"

export function useMyTimeclock() {
  const { timeClockApi } = useServices()
  return useQuery({
    queryKey: ["my-timeclock"],
    queryFn: () => timeClockApi.me(),
  })
}

export function usePunch() {
  const { timeClockApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => timeClockApi.punch(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["my-timeclock"] })
      void queryClient.invalidateQueries({ queryKey: ["shifts"] })
      void queryClient.invalidateQueries({ queryKey: ["staff-report"] })
    },
  })
}

export function useShifts(query: ShiftsQuery = {}) {
  const { timeClockApi } = useServices()
  return useQuery({
    queryKey: ["shifts", query],
    queryFn: () => timeClockApi.listShifts(query),
  })
}

export function useAdjustShift() {
  const { timeClockApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ shiftId, body }: { shiftId: string; body: AdjustShiftBody }) =>
      timeClockApi.adjustShift(shiftId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shifts"] })
      void queryClient.invalidateQueries({ queryKey: ["staff-report"] })
    },
  })
}

export function useStaffReport(query: { from?: string; to?: string } = {}) {
  const { timeClockApi } = useServices()
  return useQuery({
    queryKey: ["staff-report", query],
    queryFn: () => timeClockApi.staffReport(query),
  })
}

export function useRegisterPresenceDevice() {
  const { timeClockApi } = useServices()
  return useMutation({ mutationFn: () => timeClockApi.registerPresenceDevice() })
}

// Display: poll the rotating challenge. `refetchInterval` keeps the QR fresh.
export function usePresenceChallenge(deviceToken: string | null) {
  const { timeClockApi } = useServices()
  return useQuery({
    queryKey: ["presence-challenge", deviceToken],
    queryFn: () => timeClockApi.presenceChallenge(deviceToken as string),
    enabled: Boolean(deviceToken),
    refetchInterval: 15_000,
    retry: false,
  })
}

export function usePresencePunch() {
  const { timeClockApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (presented: string) => timeClockApi.presencePunch(presented),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["my-timeclock"] })
      void queryClient.invalidateQueries({ queryKey: ["shifts"] })
      void queryClient.invalidateQueries({ queryKey: ["staff-report"] })
    },
  })
}
