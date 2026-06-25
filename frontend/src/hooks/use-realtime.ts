import { useEffect } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

type Stream = "kds" | "floor"

// Opens an SSE stream and invalidates `queryKey` whenever `eventName` fires, so
// the matching query refetches in <1s. The stream carries no data — it is just a
// "refetch now" signal, and the data still comes through the RLS-scoped endpoint.
// Reconnects with a fresh (short-lived) token on any drop; the query's own poll
// is the fallback if the stream is down entirely.
export function useRealtimeInvalidate(stream: Stream, eventName: string, queryKey: string): void {
  const { realtimeApi } = useServices()
  const queryClient = useQueryClient()

  useEffect(() => {
    let source: EventSource | null = null
    let stopped = false
    let retry: ReturnType<typeof setTimeout> | undefined

    const connect = async () => {
      try {
        const { token } = await realtimeApi.streamToken()
        if (stopped) return
        const url =
          stream === "kds" ? realtimeApi.kdsStreamUrl(token) : realtimeApi.floorStreamUrl(token)
        source = new EventSource(url)
        source.addEventListener(eventName, () => {
          void queryClient.invalidateQueries({ queryKey: [queryKey] })
        })
        source.onerror = () => {
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
  }, [realtimeApi, queryClient, stream, eventName, queryKey])
}
