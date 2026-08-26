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

export function FinalCta() {
  const { login, register } = useAuthLinks()
  const t = COPY[useContainer().locale]

  return (
    <section className="mx-auto max-w-6xl px-5 pb-24">
      <Reveal className="relative overflow-hidden rounded-3xl border border-primary/30 bg-primary/8 px-6 py-14 text-center sm:px-12">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 h-72 w-2/3 -translate-x-1/2 rounded-[50%] bg-primary/20 blur-[100px]" />
        </div>
        <h2 className="mx-auto max-w-2xl font-display text-3xl font-bold tracking-tight text-balance sm:text-4xl">
          {t.heading}
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg text-muted-foreground">{t.sub}</p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <a href={register} className={cn(buttonVariants({ variant: "primary", size: "lg" }))}>
            {t.primary}
            <ArrowRight className="size-4" />
          </a>
          <a href={login} className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            {t.secondary}
          </a>
        </div>
      </Reveal>
    </section>
  )
}
