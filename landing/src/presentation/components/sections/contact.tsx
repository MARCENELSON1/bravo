import { useState, type FormEvent } from "react"
import { CheckCircle2 } from "lucide-react"

import { useLeadForm } from "@/presentation/hooks/use-lead-form"
import { Button } from "@/presentation/components/ui/button"
import { Reveal } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const FIELD =
  "w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-ring/40"

const COPY = {
  "es-AR": {
    eyebrow: "Contacto",
    heading: "¿Tenés varios locales? Hablemos.",
    sub: "Dejanos tus datos y te contactamos para armar el plan que necesitás.",
    successTitle: "¡Listo! Recibimos tus datos.",
    successSub: "Te vamos a escribir a la brevedad.",
    name: "Nombre",
    namePlaceholder: "Tu nombre",
    email: "Email",
    emailPlaceholder: "vos@tulocal.com",
    message: "Contanos un poco (opcional)",
    messagePlaceholder: "¿Cuántos locales tenés? ¿Qué necesitás?",
    submit: "Quiero que me contacten",
    submitting: "Enviando…",
  },
  "en-US": {
    eyebrow: "Contact",
    heading: "Got multiple locations? Let's talk.",
    sub: "Leave your details and we'll reach out to build the plan you need.",
    successTitle: "Done! We got your details.",
    successSub: "We'll be in touch shortly.",
    name: "Name",
    namePlaceholder: "Your name",
    email: "Email",
    emailPlaceholder: "you@yourrestaurant.com",
    message: "Tell us a bit (optional)",
    messagePlaceholder: "How many locations do you have? What do you need?",
    submit: "Have someone contact me",
    submitting: "Sending…",
  },
} as const

export function Contact() {
  const { status, error, submit } = useLeadForm()
  const t = COPY[useContainer().locale]
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit({ name, email, message })
  }

  return (
    <section id="contacto" className="mx-auto max-w-3xl px-5 py-20 md:py-24">
      <Reveal className="rounded-3xl border border-border bg-card p-8 sm:p-10">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">{t.eyebrow}</p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {t.heading}
          </h2>
          <p className="mt-3 text-muted-foreground">{t.sub}</p>
        </div>

        {status === "success" ? (
          <div className="mt-8 flex flex-col items-center gap-3 rounded-2xl border border-primary/30 bg-primary/8 p-8 text-center">
            <CheckCircle2 className="size-10 text-primary" />
            <p className="font-medium">{t.successTitle}</p>
            <p className="text-sm text-muted-foreground">{t.successSub}</p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mx-auto mt-8 flex max-w-md flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-name" className="text-sm font-medium">
                {t.name}
              </label>
              <input
                id="lead-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={FIELD}
                placeholder={t.namePlaceholder}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-email" className="text-sm font-medium">
                {t.email}
              </label>
              <input
                id="lead-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={FIELD}
                placeholder={t.emailPlaceholder}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-message" className="text-sm font-medium">
                {t.message}
              </label>
              <textarea
                id="lead-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className={FIELD}
                placeholder={t.messagePlaceholder}
              />
            </div>

            {error ? <p className="text-sm text-red-500">{error}</p> : null}

            <Button type="submit" size="lg" disabled={status === "submitting"} className="mt-1">
              {status === "submitting" ? t.submitting : t.submit}
            </Button>
          </form>
        )}
      </Reveal>
    </section>
  )
}
