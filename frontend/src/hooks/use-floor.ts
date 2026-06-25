import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"
import { useRealtimeInvalidate } from "@/hooks/use-realtime"

// The salon map is realtime via SSE (`floor.changed` on occupancy/total changes).
// The poll fallback (10s) also catches the paid→free transition, whose event the
// payment flow doesn't publish yet.
export function useFloor() {
  const { floorApi } = useServices()
  const query = useQuery({
    queryKey: ["floor"],
    queryFn: () => floorApi.list(),
    refetchInterval: 10000,
  })
  useRealtimeInvalidate("floor", "floor.changed", "floor")
  return query
}
