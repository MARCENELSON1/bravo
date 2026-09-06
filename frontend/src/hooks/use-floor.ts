import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"
import { fallbackInterval, useRealtimeInvalidate } from "@/hooks/use-realtime"

// The salon map is realtime via SSE (`floor.changed` on occupancy/total changes),
// cobro incluido: `_settle_order` publica el evento al pasar la orden a PAID, así
// que la mesa se ve libre al instante en vez de esperar al próximo poll. Por eso
// este intervalo pudo pasar de 10s a 30s — es red de seguridad, no el camino.
export function useFloor() {
  const { floorApi } = useServices()
  const connected = useRealtimeInvalidate("floor", "floor.changed", "floor")
  return useQuery({
    queryKey: ["floor"],
    queryFn: () => floorApi.list(),
    refetchInterval: fallbackInterval(connected),
  })
}
