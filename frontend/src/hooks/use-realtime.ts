import { useCallback, useEffect, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

type Stream = "kds" | "floor"

// Opens an SSE stream and calls `onEvent` with the event's payload whenever
// `eventName` fires. Reconnects with a fresh (short-lived) token on any drop.
// The payload is a small { key: string } signal — most callers use it to refetch
// (see `useRealtimeInvalidate`); a few need the data itself (e.g. a "table N is
// calling" toast). `onEvent` is held in a ref so re-renders don't reconnect.
//
// Devuelve si el stream está vivo. Eso es lo que deja a cada pantalla pollear
// lento mientras los avisos llegan y acelerar SOLO cuando se cortan: subir el
// intervalo a secas cambiaría carga por datos viejos justo cuando más importan.
// Arranca en `false` a propósito — hasta que el stream abre, el poll es lo único.
export function useRealtimeEvent(
  stream: Stream,
  eventName: string,
  onEvent: (payload: Record<string, string>) => void
): boolean {
  const { realtimeApi } = useServices()
  const [connected, setConnected] = useState(false)
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
        source.onopen = () => {
          if (!stopped) setConnected(true)
        }
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
          if (stopped) return
          setConnected(false)
          retry = setTimeout(() => void connect(), 3000)
        }
      } catch {
        if (stopped) return
        setConnected(false)
        retry = setTimeout(() => void connect(), 3000)
      }
    }

    void connect()
    return () => {
      stopped = true
      if (retry) clearTimeout(retry)
      source?.close()
    }
  }, [realtimeApi, stream, eventName])

  return connected
}

// Cada cuánto repreguntar una pantalla que además tiene stream. Con el stream
// vivo el poll es solo una red de seguridad (los cambios llegan por evento);
// cortado, pasa a ser la única fuente y conviene que sea rápido.
//
// ``whenConnected`` se pasa más corto SOLO si el poll dejó de ser red de seguridad
// porque tapa un cambio que nadie publica — ahí el intervalo es el techo del
// retraso real, no el de un caso degradado. Hoy ninguna pantalla está en esa
// situación: el hueco que quedaba (la mesa que se libera al cobrar) se cerró
// publicando `floor.changed` desde el flujo de pago.
export function fallbackInterval(connected: boolean, whenConnected = 30_000): number {
  return connected ? whenConnected : 5_000
}

// Invalidates `queryKey` whenever `eventName` fires, so the matching query
// refetches in <1s. The stream carries no data — just a "refetch now" signal —
// and the data still comes through the RLS-scoped endpoint. The query's own poll
// is the fallback if the stream is down entirely.
export function useRealtimeInvalidate(
  stream: Stream,
  eventName: string,
  queryKey: string
): boolean {
  const queryClient = useQueryClient()
  return useRealtimeEvent(
    stream,
    eventName,
    useCallback(() => {
      void queryClient.invalidateQueries({ queryKey: [queryKey] })
    }, [queryClient, queryKey])
  )
}
