import { useState, type FormEvent } from "react"
import { CheckCircle2 } from "lucide-react"

import { useLeadForm } from "@/presentation/hooks/use-lead-form"
import { Button } from "@/presentation/components/ui/button"
import { Reveal } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const FIELD =
  "w-full border-0 border-b border-border bg-transparent px-0 py-3 text-[0.95rem] outline-none transition-colors duration-300 placeholder:text-muted-foreground/50 focus:border-primary"

const COPY = {
  "es-AR": {
    eyebrow: "Contacto",
    heading: "¿Tenés varios locales? Hablemos.",
    sub: "Dejanos tus datos y te contactamos para armar el plan que necesitás.",
    successTitle: "¡Listo! Recibimos tus datos.",
    successSub: "Te vamos a escribir a la brevedad.",
    name: "Nombre",
    namePlaceholder: "Tu nombre",
    business: "Nombre del negocio",
    businessPlaceholder: "Cómo se llama tu negocio",
    phone: "Teléfono",
    phonePlaceholder: "+Código de área",
    email: "Email",
    emailPlaceholder: "tu@email.com",
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
    business: "Business name",
    businessPlaceholder: "What your business is called",
    phone: "Phone",
    phonePlaceholder: "+Area code",
    email: "Email",
    emailPlaceholder: "you@email.com",
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
  const [business, setBusiness] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [message, setMessage] = useState("")

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit({ name, business, email, phone, message })
  }

  return (
    <section id="contacto" className="mx-auto max-w-2xl px-5 py-28 md:py-36">
      <Reveal>
        <div className="text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">{t.eyebrow}</p>
          <h2 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl">
            {t.heading}
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">{t.sub}</p>
        </div>

        {status === "success" ? (
          <div className="mt-12 flex flex-col items-center gap-3 rounded-3xl border border-primary/30 bg-primary/8 p-10 text-center">
            <CheckCircle2 className="size-10 text-primary" />
            <p className="font-medium">{t.successTitle}</p>
            <p className="text-sm text-muted-foreground">{t.successSub}</p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mx-auto mt-12 flex max-w-md flex-col gap-7">
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
              <label htmlFor="lead-business" className="text-sm font-medium">
                {t.business}
              </label>
              <input
                id="lead-business"
                value={business}
                onChange={(e) => setBusiness(e.target.value)}
                className={FIELD}
                placeholder={t.businessPlaceholder}
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
              <label htmlFor="lead-phone" className="text-sm font-medium">
                {t.phone}
              </label>
              <input
                id="lead-phone"
                type="tel"
                inputMode="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className={FIELD}
                placeholder={t.phonePlaceholder}
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
