import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { WellnodLogo } from "@/presentation/components/brand/wellnod-mark"
import { useContainer } from "@/presentation/providers/container-provider"

const YEAR = 2026

const COPY = {
  "es-AR": {
    tagline: "El cerebro de tu local: comandas, cobros y tu copiloto en español.",
    product: "Producto",
    company: "Empresa",
    legal: "Legal",
    functions: "Funciones",
    plans: "Planes",
    faq: "Preguntas",
    contact: "Contacto",
    login: "Iniciar sesión",
    register: "Empezá gratis",
    terms: "Términos",
    privacy: "Privacidad",
    rights: `© ${YEAR} Wellnod. Todos los derechos reservados.`,
    madeIn: "Hecho en Argentina 🧉",
  },
  "en-US": {
    tagline: "Your restaurant's brain: orders, payments, and your copilot in English.",
    product: "Product",
    company: "Company",
    legal: "Legal",
    functions: "Features",
    plans: "Plans",
    faq: "FAQ",
    contact: "Contact",
    login: "Log in",
    register: "Start free trial",
    terms: "Terms",
    privacy: "Privacy",
    rights: `© ${YEAR} Wellnod. All rights reserved.`,
    madeIn: "Built for US restaurants 🇺🇸",
  },
} as const

export function Footer() {
  const { login, register } = useAuthLinks()
  const t = COPY[useContainer().locale]

  const columns = [
    {
      title: t.product,
      links: [
        { label: t.functions, href: "#producto" },
        { label: t.plans, href: "#planes" },
        { label: t.faq, href: "#preguntas" },
      ],
    },
    {
      title: t.company,
      links: [
        { label: t.contact, href: "#contacto" },
        { label: t.login, href: login },
        { label: t.register, href: register },
      ],
    },
    {
      title: t.legal,
      links: [
        { label: t.terms, href: "#" },
        { label: t.privacy, href: "#" },
      ],
    },
  ]

  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <WellnodLogo />
          <p className="mt-4 max-w-xs text-sm text-muted-foreground">{t.tagline}</p>
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
          <p>{t.rights}</p>
          <p>{t.madeIn}</p>
        </div>
      </div>
    </footer>
  )
}
