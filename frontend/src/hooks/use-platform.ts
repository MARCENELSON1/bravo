import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { PlatformPlanInput } from "@/api/types-platform"
import { useServices } from "@/services/services-context"

export function usePlatformAccess() {
  const { platformApi } = useServices()
  return useQuery({
    queryKey: ["platform-access"],
    queryFn: () => platformApi.access(),
  })
}

export function usePlatformFeatures() {
  const { platformApi } = useServices()
  return useQuery({
    queryKey: ["platform-features"],
    queryFn: () => platformApi.features(),
  })
}

export function usePlatformPlans() {
  const { platformApi } = useServices()
  return useQuery({
    queryKey: ["platform-plans"],
    queryFn: () => platformApi.listPlans(),
  })
}

export function useSavePlan() {
  const { platformApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: PlatformPlanInput) => platformApi.savePlan(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-plans"] })
    },
  })
}

export function useDeletePlan() {
  const { platformApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => platformApi.deletePlan(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-plans"] })
    },
  })
}
