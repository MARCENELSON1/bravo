import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { WellnodLogo } from "@/presentation/components/brand/wellnod-mark"

const YEAR = 2026

export function Footer() {
  const { login, register } = useAuthLinks()

  const columns = [
    {
      title: "Producto",
      links: [
        { label: "Funciones", href: "#producto" },
        { label: "Planes", href: "#planes" },
        { label: "Preguntas", href: "#preguntas" },
      ],
    },
    {
      title: "Empresa",
      links: [
        { label: "Contacto", href: "#contacto" },
        { label: "Iniciar sesión", href: login },
        { label: "Empezá gratis", href: register },
      ],
    },
    {
      title: "Legal",
      links: [
        { label: "Términos", href: "#" },
        { label: "Privacidad", href: "#" },
      ],
    },
  ]

  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <WellnodLogo />
          <p className="mt-4 max-w-xs text-sm text-muted-foreground">
            El cerebro de tu local: comandas, cobros y tu copiloto en español.
          </p>
        </div>

        {columns.map((column) => (
          <div key={column.title}>
            <p className="text-sm font-semibold">{column.title}</p>
            <ul className="mt-4 flex flex-col gap-2.5">
              {column.links.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground transition hover:text-foreground"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-5 py-6 text-sm text-muted-foreground sm:flex-row">
          <p>© {YEAR} Wellnod. Todos los derechos reservados.</p>
          <p>Hecho en Argentina 🧉</p>
        </div>
      </div>
    </footer>
  )
}
