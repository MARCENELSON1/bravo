import { useState, type AnimationEvent } from "react"
import { Menu, X } from "lucide-react"

import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { buttonVariants } from "@/presentation/components/ui/button"
import { useContainer } from "@/presentation/providers/container-provider"
import type { Locale } from "@/domain/value-objects/region"
import { cn } from "@/presentation/lib/cn"

// Los anchors son ids de sección (iguales en los dos idiomas); solo cambia la etiqueta.
const COPY: Record<Locale, {
  links: { href: string; label: string }[]
  login: string
  register: string
  home: string
  menuOpen: string
  menuClose: string
}> = {
  "es-AR": {
    links: [
      { href: "#producto", label: "Producto" },
      { href: "#como-funciona", label: "Cómo funciona" },
      { href: "#planes", label: "Planes" },
    ],
    login: "Iniciar sesión",
    register: "Empezá gratis",
    home: "Wellnod — inicio",
    menuOpen: "Abrir menú",
    menuClose: "Cerrar menú",
  },
  "en-US": {
    links: [
      { href: "#producto", label: "Product" },
      { href: "#como-funciona", label: "How it works" },
      { href: "#planes", label: "Plans" },
    ],
    login: "Log in",
    register: "Start free trial",
    home: "Wellnod — home",
    menuOpen: "Open menu",
    menuClose: "Close menu",
  },
}

// Navbar integrada: logo a la izquierda, y la navegación junto a las acciones a la
// derecha, con el mismo vidrio que los paneles del software. NO reacciona al
// scroll: mismo alto y mismo fondo, siempre.
//
// Hubo tres intentos de que reaccionara —achicarse, cambiar de fondo, aparecer y
// desaparecer— y los tres se veían como un salto. Es sticky y está en el flujo:
// cualquier cambio suyo corre el contenido de abajo, o fuerza una capa de
// composición nueva a mitad de scroll. La estabilidad vale más que el efecto.
export function Navbar() {
  const { login, register } = useAuthLinks()
  const t = COPY[useContainer().locale]
  // `open` es «está montado», no «está abierto»: al cerrar se queda montado
  // mientras corre la animación de salida, que si no no habría nada que animar.
  const [open, setOpen] = useState(false)
  const [closing, setClosing] = useState(false)
  const expanded = open && !closing

  const openMenu = () => {
    setClosing(false)
    setOpen(true)
  }

  // Con «reducir movimiento» no hay animación y `animationend` nunca llega: sin
  // este atajo el panel se quedaría montado y cerrándose para siempre.
  const closeMenu = () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setOpen(false)
      return
    }
    setClosing(true)
  }

  // Solo la animación del panel; la del contenido burbujea hasta acá y no cuenta.
  const onPanelAnimationEnd = (event: AnimationEvent<HTMLElement>) => {
    if (event.target !== event.currentTarget || !closing) return
    setOpen(false)
    setClosing(false)
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/70 backdrop-blur-xl">
      {/* A todo el ancho, no dentro del contenedor de las secciones: en una pantalla
          grande el wordmark va contra el borde izquierdo y las acciones contra el
          derecho. El padding crece un poco en pantallas anchas para que no queden
          pegados al vidrio. */}
      <div className="flex h-[4.375rem] w-full items-center justify-between gap-3 px-5 lg:px-8">
        {/* Solo el wordmark, igual que el software y que el mockup del hero. */}
        <a
          href="#top"
          aria-label={t.home}
          className="shrink-0 rounded-md transition-opacity duration-200 hover:opacity-70 focus-visible:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary"
        >
          {/* Sin `leading-none` ni empujones a mano: con el interlineado natural, el
              flex del contenedor lo centra igual que a los links de al lado. Mezclar
              los dos criterios era lo que los desalineaba. */}
          <span className="font-brand block text-3xl tracking-tight text-foreground">
            <span className="font-bold">Well</span>
            <span className="-ml-[2px] font-light text-foreground/55">nod</span>
          </span>
        </a>

        {/* Navegación y acciones, juntas a la derecha y separadas por una línea. */}
        <div className="hidden items-center gap-6 md:flex">
          <nav className="flex items-center gap-6">
            {t.links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-[0.8125rem] font-medium text-muted-foreground transition-colors duration-200 hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <span aria-hidden className="h-4 w-px bg-border" />

          <div className="flex items-center gap-1.5">
            <a href={login} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
              {t.login}
            </a>
            <a href={register} className={cn(buttonVariants({ variant: "primary", size: "sm" }))}>
              {t.register}
            </a>
          </div>
        </div>

        {/* Acciones (móvil) */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            type="button"
            onClick={() => (expanded ? closeMenu() : openMenu())}
            aria-label={expanded ? t.menuClose : t.menuOpen}
            aria-expanded={expanded}
            className="inline-flex size-9 items-center justify-center rounded-lg border border-border bg-white/[0.04] text-foreground transition hover:bg-white/[0.08] active:scale-[0.97]"
          >
            {expanded ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Menú móvil. Las filas van a sangre —el resaltado llega a los dos bordes, como
          la línea del header— y su texto arranca a la misma altura que el wordmark;
          los botones son un bloque aparte, adentro del margen. Todo en una grilla de
          48px: fila y botón miden lo mismo y usan el mismo cuerpo.

          Cuelga del borde inferior del header y está FUERA del flujo: abrirlo no
          empuja la apertura hacia abajo, se muestra encima. Por eso el vidrio va casi
          opaco —detrás ya no hay página en blanco sino el título del hero— y por eso
          no lleva línea propia arriba: la de abajo del header ya está ahí.

          Este envoltorio solo recorta. Sin él, el panel entraría desde arriba pisando
          la barra en vez de asomar por debajo. */}
      {open ? (
        <div className="absolute inset-x-0 top-full overflow-hidden md:hidden">
          <div
            onAnimationEnd={onPanelAnimationEnd}
            className={cn(
              "menu-panel border-b border-border bg-background/95 backdrop-blur-xl",
              closing && "menu-panel-closing",
            )}
          >
            <div className="menu-panel-body">
              <nav className="flex flex-col py-2">
                {t.links.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={closeMenu}
                    className="flex h-12 items-center px-5 text-[0.9375rem] font-medium text-foreground transition-colors hover:bg-white/[0.05] active:bg-white/[0.08]"
                  >
                    {link.label}
                  </a>
                ))}
              </nav>
              <div className="grid gap-2 border-t border-border px-5 pt-4 pb-5">
                <a
                  href={login}
                  className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}
                >
                  {t.login}
                </a>
                <a
                  href={register}
                  className={cn(buttonVariants({ variant: "primary", size: "lg" }), "w-full")}
                >
                  {t.register}
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  )
}
