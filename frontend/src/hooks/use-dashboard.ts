import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useDashboard(params: { from?: string; to?: string } = {}) {
  const { reportsApi } = useServices()
  return useQuery({
    queryKey: ["dashboard-summary", params],
    queryFn: () => reportsApi.getDashboard(params),
  })
}
