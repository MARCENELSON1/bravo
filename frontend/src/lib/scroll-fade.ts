import type { OverlayScrollbars } from "overlayscrollbars"

// Fade vertical proporcional al scroll: el degradé de cada borde crece desde 0 a
// medida que hay contenido oculto de ese lado. Avisa que la sección sigue, sin
// depender de que la barra de scroll esté visible.
//
// El tamaño se publica como --fade-top / --fade-bottom sobre el host; la máscara
// que los consume vive en index.css (.scroll-fade).
//
// Para el equivalente HORIZONTAL —filas de chips y pestañas— ver `lib/edge-fade`,
// que resuelve lo mismo con estado de React en vez de eventos de OverlayScrollbars.
const FADE_MAX = 28

export function updateScrollFade(instance: OverlayScrollbars) {
  const { host, viewport } = instance.elements()
  const top = Math.min(viewport.scrollTop, FADE_MAX)
  const bottomDist = viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop
  const bottom = Math.min(Math.max(bottomDist, 0), FADE_MAX)
  host.style.setProperty("--fade-top", `${top}px`)
  host.style.setProperty("--fade-bottom", `${bottom}px`)
}

// Los tres eventos que hay que escuchar para que el degradé siga al contenido:
// al montar, al cambiar el tamaño del contenido y al scrollear.
export const SCROLL_FADE_EVENTS = {
  initialized: updateScrollFade,
  updated: updateScrollFade,
  scroll: updateScrollFade,
} as const
