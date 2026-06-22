import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AdvisorQuery, UpdateAdvisorSettingsBody } from "@/api/types-advisor"
import { useServices } from "@/services/services-context"

export function useAdvisorReport(query: AdvisorQuery) {
  const { advisorApi } = useServices()
  return useQuery({
    queryKey: ["advisor-report", query],
    queryFn: () => advisorApi.report(query),
  })
}

export function useAdvisorSettings() {
  const { advisorApi } = useServices()
  return useQuery({ queryKey: ["advisor-settings"], queryFn: () => advisorApi.settings() })
}

export function useUpdateAdvisorSettings() {
  const { advisorApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: UpdateAdvisorSettingsBody) => advisorApi.updateSettings(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["advisor-settings"] })
      void queryClient.invalidateQueries({ queryKey: ["advisor-report"] })
    },
  })
}
