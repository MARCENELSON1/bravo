import { useState } from "react"
import { Menu, X } from "lucide-react"

import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { WellnodMark } from "@/presentation/components/brand/wellnod-mark"
import { buttonVariants } from "@/presentation/components/ui/button"
import { ThemeToggle } from "@/presentation/components/ui/theme-toggle"
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
      { href: "#preguntas", label: "Preguntas" },
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
      { href: "#preguntas", label: "FAQ" },
    ],
    login: "Log in",
    register: "Start free trial",
    home: "Wellnod — home",
    menuOpen: "Open menu",
    menuClose: "Close menu",
  },
}

// Navbar integrada: barra a lo ancho pegada al borde superior, con borde inferior.
// Logo a la izquierda, la navegación centrada y las acciones a la derecha.
export function Navbar() {
  const { login, register } = useAuthLinks()
  const t = COPY[useContainer().locale]
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="relative mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        {/* Logo con la misma proporción/posición que el software (hélix h-9 +
            título text-2xl, kerning pegado). */}
        <a href="#top" className="shrink-0" aria-label={t.home}>
          <span className="inline-flex items-center gap-2.5 text-foreground">
            <WellnodMark className="h-9 w-auto" />
            <span className="font-brand translate-y-0.5 text-2xl leading-none tracking-tight">
              <span className="font-bold">Well</span>
              <span className="-ml-[2px] font-light text-foreground/55">nod</span>
            </span>
          </span>
        </a>

        {/* Navegación centrada (desktop) */}
        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          {t.links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Acciones (desktop) */}
        <div className="hidden items-center gap-1.5 md:flex">
          <ThemeToggle />
          <a href={login} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
            {t.login}
          </a>
          <a href={register} className={cn(buttonVariants({ variant: "primary", size: "sm" }))}>
            {t.register}
          </a>
        </div>

        {/* Acciones (móvil) */}
        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
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
        <div className="border-t border-border bg-background/95 backdrop-blur-xl md:hidden">
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
