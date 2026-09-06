/**
 * El estado "el stream está vivo" que decide cada cuánto pollea cada pantalla.
 *
 * Es la pieza con más consecuencia y menos superficie: si se queda pegada en
 * `false` polleamos cada 5s para siempre (más carga que antes de todo esto); si
 * se queda pegada en `true` con el stream muerto, el mozo mira una pantalla
 * desactualizada hasta 30s creyendo que está al día. Ninguna de las dos rompe
 * nada visible, que es justo por qué necesita test.
 */

import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ServicesProvider } from "@/services/services-provider"
import type { Services } from "@/services/services-context"
import { fallbackInterval, useRealtimeEvent } from "@/hooks/use-realtime"

// --- Doble de EventSource: jsdom no lo trae, y además lo queremos manejable ---

class FakeEventSource {
  static instances: FakeEventSource[] = []
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  closed = false
  private listeners = new Map<string, (e: MessageEvent) => void>()

  url: string

  constructor(url: string) {
    this.url = url
    FakeEventSource.instances.push(this)
  }

  addEventListener(name: string, fn: (e: MessageEvent) => void): void {
    this.listeners.set(name, fn)
  }

  close(): void {
    this.closed = true
  }

  emit(name: string, data: unknown): void {
    this.listeners.get(name)?.({ data: JSON.stringify(data) } as MessageEvent)
  }
}

function Probe({ onEvent = () => {} }: { onEvent?: (p: Record<string, string>) => void }) {
  const connected = useRealtimeEvent("floor", "floor.changed", onEvent)
  return <span data-testid="state">{connected ? "vivo" : "cortado"}</span>
}

function renderProbe(onEvent?: (p: Record<string, string>) => void) {
  const services = {
    realtimeApi: {
      streamToken: vi.fn().mockResolvedValue({ token: "t" }),
      floorStreamUrl: (t: string) => `/floor?token=${t}`,
      kdsStreamUrl: (t: string) => `/kds?token=${t}`,
    },
  } as unknown as Services
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ServicesProvider value={services}>
        <Probe onEvent={onEvent} />
      </ServicesProvider>
    </QueryClientProvider>
  )
}

const state = () => screen.getByTestId("state").textContent

beforeEach(() => {
  FakeEventSource.instances = []
  vi.stubGlobal("EventSource", FakeEventSource)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe("useRealtimeEvent", () => {
  it("arranca cortado: hasta que el stream abre, el poll es lo único que hay", () => {
    renderProbe()
    expect(state()).toBe("cortado")
  })

  it("pasa a vivo cuando el stream abre", async () => {
    renderProbe()
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1))

    FakeEventSource.instances[0].onopen?.()

    await waitFor(() => expect(state()).toBe("vivo"))
  })

  it("vuelve a cortado cuando el stream se cae", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    renderProbe()
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1))
    FakeEventSource.instances[0].onopen?.()
    await waitFor(() => expect(state()).toBe("vivo"))

    FakeEventSource.instances[0].onerror?.()

    // Sin esto, una caída dejaría la pantalla polleando cada 30s y desactualizada.
    await waitFor(() => expect(state()).toBe("cortado"))
  })

  it("entrega el payload del evento al handler", async () => {
    const seen: Record<string, string>[] = []
    renderProbe((p) => seen.push(p))
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1))

    FakeEventSource.instances[0].emit("floor.changed", { table_id: "tb1" })

    expect(seen).toEqual([{ table_id: "tb1" }])
  })

  it("un frame malformado no rompe: entrega payload vacío", async () => {
    const seen: Record<string, string>[] = []
    renderProbe((p) => seen.push(p))
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1))

    const src = FakeEventSource.instances[0]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(src as any).listeners.get("floor.changed")?.({ data: "{no-json" } as MessageEvent)

    expect(seen).toEqual([{}])
  })

  it("cierra el stream al desmontar (si no, se filtra una conexión por pantalla)", async () => {
    const { unmount } = renderProbe()
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1))

    unmount()

    expect(FakeEventSource.instances[0].closed).toBe(true)
  })
})

describe("fallbackInterval", () => {
  it("con el stream vivo el poll es red de seguridad: lento", () => {
    expect(fallbackInterval(true)).toBe(30_000)
  })

  it("cortado el poll es la ÚNICA fuente: rápido", () => {
    expect(fallbackInterval(false)).toBe(5_000)
  })

  it("acepta un techo más corto para una pantalla que tape un cambio sin evento", () => {
    expect(fallbackInterval(true, 10_000)).toBe(10_000)
    expect(fallbackInterval(false, 10_000)).toBe(5_000)
  })
})
