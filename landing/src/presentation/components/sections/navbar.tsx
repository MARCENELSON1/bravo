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

// Navbar integrada: logo a la izquierda, navegación centrada y acciones a la
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
    <header className="sticky top-0 z-50 border-b border-black/10 bg-white/85 backdrop-blur-2xl dark:border-white/10 dark:bg-neutral-900/80">
      <div className="relative mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-5">
        {/* Solo el wordmark, igual que el software y que el mockup del hero. */}
        <a
          href="#top"
          aria-label={t.home}
          className="shrink-0 rounded-md transition-opacity duration-200 hover:opacity-70 focus-visible:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary"
        >
          {/* Sin `leading-none` ni empujones a mano: con el interlineado natural, el
              flex del contenedor lo centra igual que a los links de al lado. Mezclar
              los dos criterios era lo que los desalineaba. */}
          <span className="font-brand block text-2xl tracking-tight text-foreground">
            <span className="font-bold">Well</span>
            <span className="-ml-[2px] font-light text-foreground/55">nod</span>
          </span>
        </a>

        {/* Navegación centrada (desktop) */}
        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          {t.links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Acciones (desktop) */}
        <div className="hidden items-center gap-1.5 md:flex">
          <a href={login} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
            {t.login}
          </a>
          <a href={register} className={cn(buttonVariants({ variant: "primary", size: "sm" }))}>
            {t.register}
          </a>
        </div>

        {/* Acciones (móvil) */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            type="button"
            onClick={() => (expanded ? closeMenu() : openMenu())}
            aria-label={expanded ? t.menuClose : t.menuOpen}
            aria-expanded={expanded}
            className="inline-flex size-10 items-center justify-center rounded-xl border border-border text-foreground transition active:scale-[0.97]"
          >
            {expanded ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Menú móvil. Las filas van a sangre —el resaltado llega a los dos bordes, como
          la línea del header— y su texto arranca a la misma altura que el wordmark;
          los botones son un bloque aparte, adentro del margen. Todo en una grilla de
          48px: fila y botón miden lo mismo y usan el mismo cuerpo. */}
      {open ? (
        <div
          onAnimationEnd={onPanelAnimationEnd}
          className={cn(
            "menu-panel grid border-t border-black/10 bg-white/85 backdrop-blur-2xl md:hidden dark:border-white/10 dark:bg-neutral-900/80",
            closing && "menu-panel-closing",
          )}
        >
          {/* Dos envoltorios que la animación necesita: este recorta mientras la fila
              de grilla crece, y el de adentro baja el contenido con el panel. */}
          <div className="overflow-hidden">
            <div className="menu-panel-body">
              <nav className="flex flex-col py-2">
                {t.links.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={closeMenu}
                    className="flex h-12 items-center px-5 text-base font-medium text-foreground transition-colors hover:bg-accent active:bg-accent"
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
