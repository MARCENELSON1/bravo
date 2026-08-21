import { useState } from "react"
import { Menu, X } from "lucide-react"

import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { WellnodLogo } from "@/presentation/components/brand/wellnod-mark"
import { buttonVariants } from "@/presentation/components/ui/button"
import { ThemeToggle } from "@/presentation/components/ui/theme-toggle"
import { cn } from "@/presentation/lib/cn"

const LINKS = [
  { href: "#producto", label: "Producto" },
  { href: "#como-funciona", label: "Cómo funciona" },
  { href: "#planes", label: "Planes" },
  { href: "#preguntas", label: "Preguntas" },
]

// Navbar flotante de glass: barra redondeada separada de los bordes, con el logo a
// la izquierda, la navegación centrada y las acciones a la derecha.
export function Navbar() {
  const { login, register } = useAuthLinks()
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 px-4 pt-3">
      <div className="relative mx-auto flex h-14 max-w-5xl items-center justify-between gap-3 rounded-2xl border border-border/70 bg-background/70 pr-3 pl-4 shadow-lg shadow-black/5 backdrop-blur-xl">
        <a href="#top" className="shrink-0" aria-label="Wellnod — inicio">
          <WellnodLogo />
        </a>

        {/* Navegación centrada (desktop) */}
        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          {LINKS.map((link) => (
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
            Iniciar sesión
          </a>
          <a href={register} className={cn(buttonVariants({ variant: "primary", size: "sm" }))}>
            Empezá gratis
          </a>
        </div>

        {/* Acciones (móvil) */}
        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={open}
            className="inline-flex size-10 items-center justify-center rounded-xl border border-border text-foreground transition active:scale-[0.97]"
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Menú móvil (panel flotante) */}
      {open ? (
        <div className="mx-auto mt-2 max-w-5xl rounded-2xl border border-border bg-background/95 p-3 shadow-lg backdrop-blur-xl md:hidden">
          <nav className="flex flex-col gap-1">
            {LINKS.map((link) => (
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
              Iniciar sesión
            </a>
            <a
              href={register}
              className={cn(buttonVariants({ variant: "primary", size: "md" }), "w-full")}
            >
              Empezá gratis
            </a>
          </div>
        </div>
      ) : null}
    </header>
  )
}
