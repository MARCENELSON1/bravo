import { useEffect } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

// The kitchen board is realtime via SSE: the server pushes a `kds.changed` event
// whenever this tenant's board changes, and we refetch the RLS-scoped endpoint
// (the stream carries no data, so isolation never depends on it). A slow poll
// stays as a fallback in case the stream drops.
export function useKdsOrders() {
  const { ordersApi, realtimeApi } = useServices()
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ["kds-orders"],
    queryFn: () => ordersApi.kds(),
    refetchInterval: 20000, // fallback; SSE makes updates feel instant
  })

  useEffect(() => {
    let source: EventSource | null = null
    let stopped = false
    let retry: ReturnType<typeof setTimeout> | undefined

    const connect = async () => {
      try {
        const { token } = await realtimeApi.streamToken()
        if (stopped) return
        source = new EventSource(realtimeApi.kdsStreamUrl(token))
        source.addEventListener("kds.changed", () => {
          void queryClient.invalidateQueries({ queryKey: ["kds-orders"] })
        })
        source.onerror = () => {
          // The stream token is short-lived; on any drop reconnect with a fresh one.
          source?.close()
          source = null
          if (!stopped) retry = setTimeout(() => void connect(), 3000)
        }
      } catch {
        if (!stopped) retry = setTimeout(() => void connect(), 3000)
      }
    }

    void connect()
    return () => {
      stopped = true
      if (retry) clearTimeout(retry)
      source?.close()
    }
  }, [ordersApi, realtimeApi, queryClient])

  return query
}
