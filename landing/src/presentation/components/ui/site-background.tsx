import { useEffect, useRef } from "react"

// Cuántos estados de fondo hay definidos en el CSS ([data-mood="0"…"3"]). Se rotan
// por sección, así dos seguidas nunca quedan iguales.
const MOODS = 4

// Fondo neutro: solo luz y sombra, sin tinte. El verde queda reservado para la
// marca y los acentos. Con vida propia en dos tiempos:
//
//   1. Continuo: tres manchas muy difusas derivan solas y se desplazan con el
//      scroll a distinta velocidad (parallax por capas).
//   2. Por sección: al entrar en cada una, las manchas se reacomodan y cambian de
//      presencia con una transición larga. El color NUNCA cambia — solo posición e
//      intensidad, para que se lea como luz moviéndose y no como un semáforo.
export function SiteBackground() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return

    // --- Desplazamiento continuo con el scroll --------------------------------
    let raf = 0
    const write = () => {
      raf = 0
      const max = document.documentElement.scrollHeight - window.innerHeight
      el.style.setProperty("--scroll", max > 0 ? (window.scrollY / max).toFixed(4) : "0")
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(write)
    }
    write()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)

    // --- Estado por sección ---------------------------------------------------
    // El margen recorta el viewport a una franja central: el observador dispara
    // cuando una sección cruza la mitad de la pantalla, que es el momento en que
    // el visitante siente que entró en ella.
    const sections = Array.from(document.querySelectorAll("main > section"))
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.find((entry) => entry.isIntersecting)
        if (!visible) return
        const index = sections.indexOf(visible.target)
        if (index >= 0) el.dataset.mood = String(index % MOODS)
        // Una sección puede pedir que la marca de agua se retire: el cierre lo hace,
        // porque su título dice «Wellnod» y las dos palabras se pisaban.
        el.dataset.watermark = visible.target.hasAttribute("data-watermark") ? "hide" : "show"
      },
      { rootMargin: "-45% 0px -45% 0px" },
    )
    sections.forEach((section) => observer.observe(section))

    return () => {
      if (raf) cancelAnimationFrame(raf)
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
      observer.disconnect()
    }
  }, [])

  return (
    <div
      ref={ref}
      aria-hidden
      data-mood="0"
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      {/* Base: el gradiente de la app, semitransparente sobre el fondo del tema. */}
      <div className="absolute inset-0 opacity-40 bg-[radial-gradient(125%_125%_at_18%_12%,#f6f6f6_0%,#e9e9e9_50%,#d7d7d7_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#1d1d1d_0%,#131313_52%,#0a0a0a_100%)]" />

      {/* Tres niveles por mancha: el scroll la desplaza (--depth), la sección la
          reacomoda (.aurora-mood) y el keyframe le da la deriva lenta. Cada uno
          necesita su propio elemento: no se pueden componer tres transforms. */}
      <div className="aurora-layer" style={{ "--depth": -32 } as React.CSSProperties}>
        <div className="aurora-mood mood-a">
          <div className="aurora aurora-a" />
        </div>
      </div>
      <div className="aurora-layer" style={{ "--depth": -85 } as React.CSSProperties}>
        <div className="aurora-mood mood-b">
          <div className="aurora aurora-b" />
        </div>
      </div>
      <div className="aurora-layer" style={{ "--depth": -15 } as React.CSSProperties}>
        <div className="aurora-mood mood-c">
          <div className="aurora aurora-c" />
        </div>
      </div>


      {/* Marca de agua: el wordmark en grande, detrás de todo. Se corre apenas con
          el scroll para que no quede clavada como una calcomanía. */}
      <div className="aurora-layer" style={{ "--depth": -18 } as React.CSSProperties}>
        <div className="absolute inset-0 grid place-items-center">
          <span className="watermark">Wellnod</span>
        </div>
      </div>

      {/* Viñeta: cierra los bordes y concentra la atención en el centro. */}
      <div className="vignette" />

      {/* Grano fino, igual que en la app. Va último: unifica todas las capas. */}
      <div className="bg-grain absolute inset-0 opacity-[0.12] mix-blend-overlay" />
    </div>
  )
}
