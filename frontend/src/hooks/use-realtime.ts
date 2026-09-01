import { useEffect, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

type Stream = "kds" | "floor"

// Opens an SSE stream and calls `onEvent` with the event's payload whenever
// `eventName` fires. Reconnects with a fresh (short-lived) token on any drop.
// The payload is a small { key: string } signal — most callers use it to refetch
// (see `useRealtimeInvalidate`); a few need the data itself (e.g. a "table N is
// calling" toast). `onEvent` is held in a ref so re-renders don't reconnect.
export function useRealtimeEvent(
  stream: Stream,
  eventName: string,
  onEvent: (payload: Record<string, string>) => void
): void {
  const { realtimeApi } = useServices()
  const handlerRef = useRef(onEvent)
  useEffect(() => {
    handlerRef.current = onEvent
  })

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
        source.addEventListener(eventName, (event: MessageEvent) => {
          let payload: Record<string, string> = {}
          try {
            payload = JSON.parse(event.data) as Record<string, string>
          } catch {
            // Malformed data frame — deliver an empty payload rather than throw.
          }
          handlerRef.current(payload)
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
  }, [realtimeApi, stream, eventName])
}

// Invalidates `queryKey` whenever `eventName` fires, so the matching query
// refetches in <1s. The stream carries no data — just a "refetch now" signal —
// and the data still comes through the RLS-scoped endpoint. The query's own poll
// is the fallback if the stream is down entirely.
export function useRealtimeInvalidate(stream: Stream, eventName: string, queryKey: string): void {
  const queryClient = useQueryClient()
  useRealtimeEvent(stream, eventName, () => {
    void queryClient.invalidateQueries({ queryKey: [queryKey] })
  })
}
