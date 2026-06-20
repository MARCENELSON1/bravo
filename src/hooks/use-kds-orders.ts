import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

// The kitchen board polls every 5s (cuasi tiempo real for the MVP; SSE/WS later).
export function useKdsOrders() {
  const { ordersApi } = useServices()
  return useQuery({
    queryKey: ["kds-orders"],
    queryFn: () => ordersApi.kds(),
    refetchInterval: 5000,
  })
}
