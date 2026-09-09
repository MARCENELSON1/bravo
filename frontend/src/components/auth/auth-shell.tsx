import { useEffect, useRef } from "react"
import { useLocation, useOutlet } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Check } from "lucide-react"

import { AppBackground } from "@/components/shell/app-background"
import { GLASS_SURFACE } from "@/components/ui/glass-card"
import { cn } from "@/lib/utils"

// Marco de las pantallas de identidad. Es un layout route: NO se desmonta cuando
// cambia la ruta hija, y de ahí sale todo lo demás.
//
// Lo permanente vive acá —el fondo, el relato de marca, la tarjeta de vidrio— y lo
// único que cambia es el contenido de la tarjeta, que sale por el <Outlet />. Por
// eso pasar de iniciar sesión a crear comercio no parpadea: el vidrio nunca se va,
// no hay nada que desaparezca y vuelva a aparecer.
//
// Antes cada pantalla montaba su propia copia de todo esto. Cambiar de ruta las
// destruía y las volvía a crear: el fondo reiniciaba sus animaciones, la tarjeta
// entera se fundía a cero y volvía, y hubo que sostener con timers, alturas
// congeladas y avisos por `state` una continuidad que la estructura no daba. Nada
// de eso hace falta acá.

// Qué rutas usan la tarjeta ancha. El alta de comercio pide más lugar que el resto:
// cinco campos contra tres.
const WIDE_PATHS = new Set(["/onboarding"])

// El wordmark, con la misma receta que la navbar de la landing.
function Wordmark() {
  return (
    <span className="font-heading text-3xl tracking-tight text-foreground">
      <span className="font-bold">Well</span>
      <span className="-ml-[2px] font-light text-foreground/55">nod</span>
    </span>
  )
}

const BULLETS = ["shift", "business", "decisions"] as const

export function AuthShell() {
  const { pathname } = useLocation()
  const { t, i18n } = useTranslation()
  const wide = WIDE_PATHS.has(pathname)
  // El ELEMENTO de la ruta, no el componente <Outlet />: este último lee el
  // contexto en cada render, así que la copia que se está yendo mostraría ya la
  // pantalla nueva —aparecía, se fundía y volvía—. Con el elemento, cada copia se
  // queda con su contenido.
  const outlet = useOutlet()

  // Al cambiar de idioma se reinicia la cascada de entrada, para que el texto
  // aparezca en el idioma nuevo en vez de reemplazarse de golpe.
  //
  // Se reinicia la animación en lugar de remontar el contenido: remontar destruiría
  // el formulario y borraría lo que la persona venía escribiendo. Sacar la clase,
  // forzar el recálculo de layout y volver a ponerla es lo que hace que el navegador
  // considere la animación como nueva.
  const bodyRef = useRef<HTMLDivElement>(null)
  const brandRef = useRef<HTMLElement>(null)
  const firstRender = useRef(true)
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    for (const el of [brandRef.current, bodyRef.current]) {
      if (!el) continue
      el.classList.remove("auth-in")
      void el.offsetWidth
      el.classList.add("auth-in")
    }
  }, [i18n.language])

  return (
    <div className="relative min-h-svh">
      {/* El fondo de siempre: neutro, con viñeta y sin textura. Acá se ve directo,
          sin los paneles de vidrio que en la consola lo filtran. */}
      <AppBackground scene="identity" />

      {/* El ancho lo maneja el CSS (ver .auth-grid): al cambiar `data-wide` la
          tarjeta se ensancha con una transición, sin que nada se desmonte. */}
      <div
        data-wide={wide}
        data-dense={wide}
        className="auth-grid mx-auto min-h-svh max-w-6xl items-center px-5 py-10"
      >
        {/* Relato de marca. Se esconde en pantallas angostas: ahí el formulario es
            todo lo que importa y el discurso ya lo leyeron en la landing. */}
        <section ref={brandRef} className="auth-in hidden flex-col lg:flex">
          <Wordmark />

          <h1 className="font-heading mt-10 text-4xl font-bold tracking-tight text-balance text-foreground">
            {t("auth.brandTitleBefore")}
            <span className="text-primary">{t("auth.brandTitleHighlight")}</span>.
          </h1>
          <p className="mt-4 max-w-md text-base text-muted-foreground">{t("auth.brandSubtitle")}</p>

          <ul className="mt-8 flex max-w-md flex-col gap-3">
            {BULLETS.map((key) => (
              <li key={key} className="flex gap-3">
                <Check className="mt-1 size-4 shrink-0 text-primary" />
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {t(`auth.bullets.${key}.label`)}
                  </span>
                  {" — "}
                  {t(`auth.bullets.${key}.text`)}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <div className="auth-card">
          {/* En angosto el wordmark encabeza el formulario; en ancho ya está en la
              columna de marca y repetirlo sería decir la marca dos veces. */}
          <div className="mb-6 flex justify-center lg:hidden">
            <Wordmark />
          </div>

          {/* La tarjeta de vidrio, permanente. Sin `layout`: anima el alto escalando
              la caja, y eso deforma el texto de adentro mientras dura. El alto ya lo
              igualan las dos pantallas por CSS (.auth-panel), así que no hay nada
              que animar. */}
          <div
            className={cn(
              GLASS_SURFACE,
              "auth-panel shadow-xl shadow-black/5 dark:shadow-black/20"
            )}
          >
            {/* La transición es un fundido de entrada y nada más. Solo opacidad: es
                lo único que se puede animar acá sin consecuencias, porque no
                participa del layout — ningún fundido puede correr la tarjeta ni el
                texto de al lado.

                Sin animación de SALIDA a propósito. La copia que se iba seguía en
                pantalla mientras el ancho ya era el de la pantalla nueva: el
                formulario largo quedaba apretado en el ancho del login y se
                desbordaba de la tarjeta. Se veía como un destello de un cuadro mal
                armado.

                Cambiar de `key` alcanza: React desmonta lo viejo y monta lo nuevo,
                que entra con su fundido. */}
            {/* La `key` es lo que dispara el barrido: al cambiar de ruta el
                elemento se monta de nuevo y su animación CSS corre de cero. */}
            <div key={pathname} ref={bodyRef} className="auth-body auth-in">
              {outlet}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
