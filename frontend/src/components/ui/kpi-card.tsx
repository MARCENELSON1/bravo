import type { CSSProperties } from "react"

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
        "@container flex flex-col gap-1 p-4",
        variant === "card" ? "rounded-xl border border-border" : "bg-card",
        // Va después de la variante: entre dos utilidades del mismo tipo gana la
        // última, que es lo que resuelve `cn`.
        positive && (variant === "card" ? "border-primary/30 bg-primary/8" : "bg-primary/12")
      )}
    >
      <span className="text-xs text-muted-foreground">{label}</span>
      {/* El número entra SIEMPRE en un renglón: ni se parte ni se pasa del borde.

          Un importe no tiene por dónde cortarse —"$ 212.400.770,00" es un solo
          bloque—, así que a cuerpo fijo se salía de la tarjeta en dos columnas de
          teléfono. Acá el cuerpo se calcula: la tarjeta se declara contenedor, y el
          tamaño es el ancho disponible dividido por lo que mide el número.

          Las dos mitades del cálculo importan. `100cqi` es el ancho de SU tarjeta y
          no el de la ventana: en la grilla de tres columnas de escritorio hay lugar y
          el número topea en el máximo de siempre; en una columna angosta baja hasta
          entrar. Y `--len` es la cantidad de caracteres, porque un ancho fijo no
          alcanza: dividir solo por el contenedor daría el mismo cuerpo a "63%" que a
          un importe de doce dígitos.

          El 0.62 es cuánto ocupa un carácter, en cuadratines. Está por encima del
          avance real de las cifras tabulares —0.6— y bastante por encima del de los
          separadores, así que el cálculo se queda corto y nunca largo: el número
          puede salir un pelo más chico de lo que entraría, jamás más grande. */}
      <span
        style={{ "--len": value.length } as CSSProperties}
        className={cn(
          "text-[min(1.25rem,calc(100cqi/(var(--len)*0.62)))] font-semibold whitespace-nowrap tabular-nums",
          negative ? "text-destructive" : "text-foreground"
        )}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  )
}
