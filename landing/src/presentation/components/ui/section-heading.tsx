import { Reveal } from "@/presentation/components/ui/reveal"
import { cn } from "@/presentation/lib/cn"

// Encabezado de sección: volanta, título y bajada. Estaba repetido casi idéntico
// en seis secciones; acá vive una sola vez, así el ritmo tipográfico es el mismo
// en toda la página.
export function SectionHeading({
  eyebrow,
  heading,
  sub,
  align = "center",
  className,
}: {
  eyebrow: string
  heading: string
  sub?: string
  align?: "center" | "start"
  className?: string
}) {
  const centered = align === "center"
  return (
    <Reveal className={cn(centered && "mx-auto max-w-3xl text-center", className)}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
      <h2 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl">
        {heading}
      </h2>
      {sub ? (
        <p
          className={cn(
            "mt-5 text-lg leading-relaxed text-muted-foreground text-balance",
            centered ? "mx-auto max-w-2xl" : "max-w-xl",
          )}
        >
          {sub}
        </p>
      ) : null}
    </Reveal>
  )
}
