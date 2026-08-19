import { useEffect, type RefObject } from "react"
import type { OverlayScrollbarsComponentRef } from "overlayscrollbars-react"

// Revela la scrollbar (marca data-peek en el host) cuando el cursor está cerca del
// borde donde vive: derecha (vertical) o abajo (horizontal). Escucha el
// pointermove SOLO sobre el propio host, así una barra no reacciona a lo que pasa
// en otro panel. El fade lo da el CSS ([data-peek] .os-scrollbar). Complementa el
// autoHide "scroll".
export function useEdgePeek(ref: RefObject<OverlayScrollbarsComponentRef | null>) {
  useEffect(() => {
    const host = ref.current?.getElement()
    if (!host) return

    const EDGE = 52
    const onMove = (e: PointerEvent) => {
      const r = host.getBoundingClientRect()
      const nearRight = e.clientX >= r.right - EDGE
      const nearBottom = e.clientY >= r.bottom - EDGE
      host.toggleAttribute("data-peek", nearRight || nearBottom)
    }
    const clear = () => host.removeAttribute("data-peek")

    host.addEventListener("pointermove", onMove)
    host.addEventListener("pointerleave", clear)
    return () => {
      host.removeEventListener("pointermove", onMove)
      host.removeEventListener("pointerleave", clear)
    }
  }, [ref])
}
