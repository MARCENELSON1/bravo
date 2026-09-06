import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"
import { fallbackInterval, useRealtimeInvalidate } from "@/hooks/use-realtime"

// The salon map is realtime via SSE (`floor.changed` on occupancy/total changes).
//
// **El poll NO se puede aflojar todavía**, y por eso queda en 10s con el stream
// vivo (el resto de las pantallas con stream van a 30s). El cobro libera la mesa
// —`_settle_order` cierra la sesión— pero no publica `floor.changed`, así que la
// transición pagado→libre la ve SOLO este poll: subirlo es demorar hasta ese
// tanto en que la mesa se muestre libre. Lo que lo destraba es publicar el evento
// en el flujo de pago; recién ahí este intervalo pasa a ser red de seguridad.
export function useFloor() {
  const { floorApi } = useServices()
  const connected = useRealtimeInvalidate("floor", "floor.changed", "floor")
  return useQuery({
    queryKey: ["floor"],
    queryFn: () => floorApi.list(),
    refetchInterval: fallbackInterval(connected, 10_000),
  })
}
