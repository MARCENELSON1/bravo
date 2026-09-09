import { heroTitle } from "@/presentation/components/sections/hero"
import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { useContainer } from "@/presentation/providers/container-provider"

const YEAR = 2026

// Los canales reales, no traducibles: el mismo usuario y el mismo buzón en las dos
// regiones. Están acá y no en COPY para que no se dupliquen por idioma.
const INSTAGRAM = "wellnodhq"
const EMAIL = "wellnodsupport@gmail.com"

const COPY = {
  "es-AR": {
    company: "Empresa",
    legal: "Legal",
    contact: "Contacto",
    login: "Iniciar sesión",
    product: "Producto",
    plans: "Planes",
    terms: "Términos",
    privacy: "Privacidad",
    rights: `© ${YEAR} Wellnod. Todos los derechos reservados.`,
    madeIn: "Hecho en Argentina",
  },
  "en-US": {
    company: "Company",
    legal: "Legal",
    contact: "Contact",
    login: "Log in",
    product: "Product",
    plans: "Plans",
    terms: "Terms",
    privacy: "Privacy",
    rights: `© ${YEAR} Wellnod. All rights reserved.`,
    madeIn: "Built for US restaurants",
  },
} as const

// Cambia la región del display y persiste la elección en la cookie que lee el
// Worker de Cloudflare (override del geo-routing). Sin JS, el <a> igual navega.
function chooseRegion(target: "ar" | "intl") {
  document.cookie = `wellnod_region=${target}; path=/; max-age=31536000; samesite=lax`
}

export function Footer() {
  const { login } = useAuthLinks()
  const { locale, region } = useContainer()
  const t = COPY[locale]
  const toIntl = region === "AR"
  const switchHref = toIntl ? "/en/" : "/"
  const switchLabel = toIntl ? "English · USD" : "Español · ARS"

  const columns = [
    {
      title: t.contact,
      wide: true,
      links: [
        { label: `@${INSTAGRAM}`, href: `https://instagram.com/${INSTAGRAM}` },
        { label: EMAIL, href: `mailto:${EMAIL}` },
      ],
    },
    {
      title: t.company,
      // Los anchors son ids de sección, iguales en los dos idiomas (ver navbar).
      links: [
        { label: t.login, href: login },
        { label: t.product, href: "#producto" },
        { label: t.plans, href: "#planes" },
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
    <footer className="border-t border-border/60">
      {/* En móvil son dos columnas. La marca y Contacto ocupan la fila entera —la
          bajada y el mail son largos y en media columna se parten—; Empresa y Legal,
          que son de una o dos palabras, van una al lado de la otra. */}
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-x-8 gap-y-10 px-5 py-12 sm:gap-12 sm:py-20 lg:grid-cols-4">
        <div className="col-span-2 sm:col-span-1">
          <span className="font-brand block text-2xl tracking-tight text-foreground">
            <span className="font-bold">Well</span>
            <span className="-ml-[2px] font-light text-foreground/55">nod</span>
          </span>
          {/* La misma frase que el título del hero, para que el cierre repita la
              promesa con la que abre la página. */}
          <p className="mt-4 max-w-xs text-sm text-muted-foreground">{heroTitle(locale)}</p>
        </div>

        {columns.map((column) => (
          <div key={column.title} className={column.wide ? "col-span-2 sm:col-span-1" : undefined}>
            <p className="text-sm font-semibold">{column.title}</p>
            <ul className="mt-5 flex flex-col gap-3">
              {column.links.map((link) => {
                // Instagram se va del sitio; el resto navega o abre el correo.
                const external = link.href.startsWith("http")
                return (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      target={external ? "_blank" : undefined}
                      rel={external ? "noreferrer" : undefined}
                      className="text-sm break-all text-muted-foreground transition hover:text-foreground"
                    >
                      {link.label}
                    </a>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-border/60">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-5 py-6 text-sm text-muted-foreground sm:flex-row">
          <p>{t.rights}</p>
          <div className="flex items-center gap-4">
            <a
              href={switchHref}
              onClick={() => chooseRegion(toIntl ? "intl" : "ar")}
              className="rounded-full border border-border px-3 py-1 text-xs font-medium transition hover:text-foreground"
            >
              {switchLabel}
            </a>
            <p>{t.madeIn}</p>
          </div>
        </div>
      </div>
    </footer>
  )
}
