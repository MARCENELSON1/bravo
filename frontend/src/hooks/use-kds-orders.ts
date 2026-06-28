import { useQuery } from "@tanstack/react-query"

import type { Station } from "@/api/types-operations"
import { useServices } from "@/services/services-context"
import { useRealtimeInvalidate } from "@/hooks/use-realtime"

// The kitchen/bar board is realtime via SSE: the server pushes `kds.changed`
// whenever this tenant's board changes and we refetch the RLS-scoped endpoint. A
// slow poll stays as a fallback in case the stream drops. Pass a `station` to get
// just that board's orders; the realtime invalidation is keyed on the shared
// `["kds-orders"]` prefix so any station's query refetches on a change.
export function useKdsOrders(station?: Station) {
  const { ordersApi } = useServices()
  const query = useQuery({
    queryKey: station ? ["kds-orders", station] : ["kds-orders"],
    queryFn: () => ordersApi.kds(station),
    refetchInterval: 20000, // fallback; SSE makes updates feel instant
  })
  useRealtimeInvalidate("kds", "kds.changed", "kds-orders")
  return query
}
