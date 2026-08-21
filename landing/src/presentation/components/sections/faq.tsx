import { useState } from "react"
import { ChevronDown } from "lucide-react"

import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { Reveal } from "@/presentation/components/ui/reveal"
import { cn } from "@/presentation/lib/cn"

export function Faq() {
  const { faqs } = useLandingContent()
  const [openId, setOpenId] = useState<string | null>(null)

  return (
    <section id="preguntas" className="mx-auto max-w-3xl px-5 py-20 md:py-24">
      <Reveal className="text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-primary">Preguntas</p>
        <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-balance sm:text-4xl">
          Lo que se suele preguntar
        </h2>
      </Reveal>

      <div className="mt-12 flex flex-col gap-3">
        {faqs.map((faq) => {
          const open = openId === faq.id
          return (
            <div key={faq.id} className="rounded-2xl border border-border bg-card">
              <button
                type="button"
                onClick={() => setOpenId(open ? null : faq.id)}
                aria-expanded={open}
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
              >
                <span className="font-medium">{faq.question}</span>
                <ChevronDown
                  className={cn(
                    "size-5 shrink-0 text-muted-foreground transition-transform duration-200",
                    open && "rotate-180",
                  )}
                />
              </button>
              <div
                className={cn(
                  "grid overflow-hidden transition-all duration-300 ease-out",
                  open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
                )}
              >
                <div className="min-h-0">
                  <p className="px-5 pb-5 text-sm leading-relaxed text-muted-foreground">
                    {faq.answer}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
