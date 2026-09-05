import { Fragment } from "react"
import { ArrowRight } from "lucide-react"

import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { buttonVariants } from "@/presentation/components/ui/button"
import { Reveal } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"
import { cn } from "@/presentation/lib/cn"

const COPY = {
  "es-AR": {
    heading: "Empezá a operar tu local con Wellnod hoy",
    sub: "Creá tu cuenta gratis en minutos. Sin tarjeta, sin instalaciones.",
    primary: "Empezá gratis",
    secondary: "Ya tengo cuenta",
  },
  "en-US": {
    heading: "Start running your restaurant with Wellnod today",
    sub: "Start your 30-day free trial in minutes. Card required, cancel anytime.",
    primary: "Start free trial",
    secondary: "I already have an account",
  },
} as const

const BRAND = "Wellnod"

// Pinta el nombre de la marca dentro de una frase, sin meter markup en la copia.
function withBrand(text: string) {
  return text.split(BRAND).map((part, i, all) => (
    <Fragment key={i}>
      {part}
      {i < all.length - 1 ? <span className="text-primary">{BRAND}</span> : null}
    </Fragment>
  ))
}

export function FinalCta() {
  const { login, register } = useAuthLinks()
  const t = COPY[useContainer().locale]

  return (
    <section data-watermark="hide" className="border-t border-border/60">
      <div className="mx-auto max-w-4xl overflow-hidden px-5 py-32 text-center md:py-40">
        {/* Tres tiempos: primero sube el titular, después la bajada y al final los
            botones. Todo junto se leía como un bloque que aparece; escalonado se
            lee como algo que se arma. */}
        <Reveal anim="left">
          <h2 className="mx-auto max-w-3xl font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-6xl">
            {withBrand(t.heading)}
          </h2>
        </Reveal>
        <Reveal anim="left" delay={260}>
          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">{t.sub}</p>
        </Reveal>
        <Reveal anim="left" delay={440} className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
          <a href={register} className={cn(buttonVariants({ variant: "primary", size: "lg" }))}>
            {t.primary}
            <ArrowRight className="size-4" />
          </a>
          <a href={login} className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            {t.secondary}
          </a>
        </Reveal>
      </div>
    </section>
  )
}
