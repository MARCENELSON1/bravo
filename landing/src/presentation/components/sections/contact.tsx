import { useState, type FormEvent } from "react"
import { CheckCircle2 } from "lucide-react"

import { useLeadForm } from "@/presentation/hooks/use-lead-form"
import { Button } from "@/presentation/components/ui/button"
import { Reveal } from "@/presentation/components/ui/reveal"

const FIELD =
  "w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-ring/40"

export function Contact() {
  const { status, error, submit } = useLeadForm()
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
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">Contacto</p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            ¿Tenés varios locales? Hablemos.
          </h2>
          <p className="mt-3 text-muted-foreground">
            Dejanos tus datos y te contactamos para armar el plan que necesitás.
          </p>
        </div>

        {status === "success" ? (
          <div className="mt-8 flex flex-col items-center gap-3 rounded-2xl border border-primary/30 bg-primary/8 p-8 text-center">
            <CheckCircle2 className="size-10 text-primary" />
            <p className="font-medium">¡Listo! Recibimos tus datos.</p>
            <p className="text-sm text-muted-foreground">Te vamos a escribir a la brevedad.</p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mx-auto mt-8 flex max-w-md flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-name" className="text-sm font-medium">
                Nombre
              </label>
              <input
                id="lead-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={FIELD}
                placeholder="Tu nombre"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-email" className="text-sm font-medium">
                Email
              </label>
              <input
                id="lead-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={FIELD}
                placeholder="vos@tulocal.com"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="lead-message" className="text-sm font-medium">
                Contanos un poco (opcional)
              </label>
              <textarea
                id="lead-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className={FIELD}
                placeholder="¿Cuántos locales tenés? ¿Qué necesitás?"
              />
            </div>

            {error ? <p className="text-sm text-red-500">{error}</p> : null}

            <Button type="submit" size="lg" disabled={status === "submitting"} className="mt-1">
              {status === "submitting" ? "Enviando…" : "Quiero que me contacten"}
            </Button>
          </form>
        )}
      </Reveal>
    </section>
  )
}
