import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"
import { useRealtimeInvalidate } from "@/hooks/use-realtime"

// The kitchen board is realtime via SSE: the server pushes `kds.changed` whenever
// this tenant's board changes and we refetch the RLS-scoped endpoint. A slow poll
// stays as a fallback in case the stream drops.
export function useKdsOrders() {
  const { ordersApi } = useServices()
  const query = useQuery({
    queryKey: ["kds-orders"],
    queryFn: () => ordersApi.kds(),
    refetchInterval: 20000, // fallback; SSE makes updates feel instant
  })
  useRealtimeInvalidate("kds", "kds.changed", "kds-orders")
  return query
}
