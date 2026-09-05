import { useState } from "react"
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
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-black/10 bg-white/60 backdrop-blur-2xl dark:border-white/10 dark:bg-black/30">
      <div className="relative mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        {/* Solo el wordmark, igual que el software y que el mockup del hero. */}
        <a href="#top" className="shrink-0" aria-label={t.home}>
          <span className="font-brand block translate-y-0.5 text-xl leading-none tracking-tight text-foreground">
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
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? t.menuClose : t.menuOpen}
            aria-expanded={open}
            className="inline-flex size-10 items-center justify-center rounded-xl border border-border text-foreground transition active:scale-[0.97]"
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Menú móvil (integrado, a lo ancho) */}
      {open ? (
        <div className="border-t border-black/10 bg-white/60 backdrop-blur-2xl md:hidden dark:border-white/10 dark:bg-black/30">
          <div className="mx-auto max-w-6xl px-4 py-3 sm:px-6">
            <nav className="flex flex-col gap-1">
              {t.links.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-accent hover:text-foreground"
                >
                  {link.label}
                </a>
              ))}
            </nav>
            <div className="mt-3 flex flex-col gap-2 border-t border-border pt-3">
              <a
                href={login}
                className={cn(buttonVariants({ variant: "outline", size: "md" }), "w-full")}
              >
                {t.login}
              </a>
              <a
                href={register}
                className={cn(buttonVariants({ variant: "primary", size: "md" }), "w-full")}
              >
                {t.register}
              </a>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  )
}
