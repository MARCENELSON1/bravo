import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useDashboard() {
  const { reportsApi } = useServices()
  return useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => reportsApi.getDashboard(),
  })
}
