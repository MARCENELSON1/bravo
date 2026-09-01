import { useEffect, useState, type RefObject } from "react"
import type { OverlayScrollbarsComponentRef } from "overlayscrollbars-react"

export interface Edges {
  start: boolean
  end: boolean
}

// ¿Queda contenido fuera de vista a los costados de una fila que scrollea en
// horizontal? Con eso se difumina ese borde en vez de cortarlo en seco, que es
// la única señal honesta de "esto sigue" cuando no hay mouse (tablet) ni se está
// tocando la barra de scroll.
export function useEdgeFade(ref: RefObject<OverlayScrollbarsComponentRef | null>): Edges {
  const [edges, setEdges] = useState<Edges>({ start: false, end: false })

  useEffect(() => {
    let raf = 0
    let viewport: HTMLElement | null = null
    let observer: ResizeObserver | null = null

    const update = () => {
      if (!viewport) return
      const max = viewport.scrollWidth - viewport.clientWidth
      setEdges({ start: viewport.scrollLeft > 1, end: viewport.scrollLeft < max - 1 })
    }

    // OverlayScrollbars se inicializa con `defer`, así que en el primer render
    // todavía no existe el viewport: reintentamos hasta que esté.
    const attach = () => {
      viewport = ref.current?.osInstance()?.elements().viewport ?? null
      if (!viewport) {
        raf = requestAnimationFrame(attach)
        return
      }
      viewport.addEventListener("scroll", update, { passive: true })
      observer = new ResizeObserver(update)
      observer.observe(viewport)
      update()
    }
    attach()

    return () => {
      cancelAnimationFrame(raf)
      viewport?.removeEventListener("scroll", update)
      observer?.disconnect()
    }
  }, [ref])

  return edges
}

// Máscara que desvanece el borde con contenido oculto. Las clases van literales
// (y no armadas por concatenación) para que Tailwind las vea al compilar.
export function edgeFadeClass({ start, end }: Edges): string {
  if (start && end)
    return "[mask-image:linear-gradient(to_right,transparent_0,black_1.5rem,black_calc(100%-1.5rem),transparent_100%)]"
  if (end) return "[mask-image:linear-gradient(to_right,black_calc(100%-1.5rem),transparent_100%)]"
  if (start) return "[mask-image:linear-gradient(to_right,transparent_0,black_1.5rem)]"
  return ""
}
