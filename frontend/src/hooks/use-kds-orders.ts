import { useQuery } from "@tanstack/react-query"

import type { Station } from "@/api/types-operations"
import { useServices } from "@/services/services-context"
import { fallbackInterval, useRealtimeInvalidate } from "@/hooks/use-realtime"

// The kitchen/bar board is realtime via SSE: the server pushes `kds.changed`
// whenever this tenant's board changes and we refetch the RLS-scoped endpoint.
// Pass a `station` to get just that board's orders; the realtime invalidation is
// keyed on the shared `["kds-orders"]` prefix so any station's query refetches on
// a change.
//
// Acá el poll sí es pura red de seguridad, así que va lento con el stream vivo y
// rápido cuando se corta: el board lista ítems HELD/SENT/PREPARING, y todo lo que
// mueve esos estados (marchar, disparar un curso, avanzar) publica `kds.changed`.
// El cobro no los toca, que es el hueco que sí tiene el plano.
export function useKdsOrders(station?: Station) {
  const { ordersApi } = useServices()
  const connected = useRealtimeInvalidate("kds", "kds.changed", "kds-orders")
  return useQuery({
    queryKey: station ? ["kds-orders", station] : ["kds-orders"],
    queryFn: () => ordersApi.kds(station),
    refetchInterval: fallbackInterval(connected),
  })
}
