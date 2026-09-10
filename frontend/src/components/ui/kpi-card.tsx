import { cn } from "@/lib/utils"

// Un número grande con su etiqueta. Estaba definido dos veces —Asesor y Analítica—
// idéntico salvo el fondo, que es justo lo que hacía que las dos pantallas se
// vieran iguales. Acá queda una sola definición con dos presentaciones:
//
//   "card"  tarjeta suelta, con su borde. Para una grilla de tarjetas.
//   "cell"  celda plana. Para ir dentro de un panel único con divisiones finas.
export function KpiCard({
  label,
  value,
  hint,
  negative,
  positive,
  variant = "card",
}: {
  label: string
  value: string
  /** Aclaración bajo el número (unidad, comparación, por qué está bloqueado). */
  hint?: string
  /** Pinta el número en rojo: sirve para un margen o un saldo negativo. */
  negative?: boolean
  /** Tiñe la celda de verde: el número no es solo un dato, es una buena noticia. */
  positive?: boolean
  variant?: "card" | "cell"
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 p-4",
        variant === "card" ? "rounded-xl border border-border" : "bg-card",
        // Va después de la variante: entre dos utilidades del mismo tipo gana la
        // última, que es lo que resuelve `cn`.
        positive && (variant === "card" ? "border-primary/30 bg-primary/8" : "bg-primary/12")
      )}
    >
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "text-lg font-semibold tabular-nums sm:text-xl",
          negative ? "text-destructive" : "text-foreground"
        )}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  )
}
