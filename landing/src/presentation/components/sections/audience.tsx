import { useContainer } from "@/presentation/providers/container-provider"

const COPY = {
  "es-AR": {
    label: "Pensado para la gastronomía argentina",
    types: ["Restaurantes", "Bares", "Cafés", "Food trucks", "Cervecerías", "Cadenas"],
  },
  "en-US": {
    label: "Built for US restaurants",
    types: ["Restaurants", "Bars", "Cafés", "Food trucks", "Breweries", "Chains"],
  },
} as const

// Cinta continua de rubros. Antes eran seis píldoras estáticas centradas; como
// cinta ocupan menos y el movimiento sugiere "hay más" sin listar de más. El
// track está duplicado: desplazarlo un 50 % vuelve al inicio sin salto. Se frena
// al pasar el mouse o al tabular, y con "reducir movimiento" queda quieta.
export function Audience() {
  const t = COPY[useContainer().locale]
  const loop = [...t.types, ...t.types]

  return (
    <section className="border-y border-border/60 py-12">
      <p className="text-center text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {t.label}
      </p>

      <div
        className="marquee relative mt-7 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8rem,black_calc(100%-8rem),transparent)]"
        aria-hidden
      >
        <ul className="marquee-track flex w-max items-center gap-14 pr-14">
          {loop.map((type, i) => (
            <li
              key={`${type}-${i}`}
              className="font-display text-2xl font-semibold tracking-tight whitespace-nowrap text-muted-foreground/60 sm:text-3xl"
            >
              {type}
            </li>
          ))}
        </ul>
      </div>

      {/* La cinta es decorativa; la lista real queda accesible para lectores. */}
      <ul className="sr-only">
        {t.types.map((type) => (
          <li key={type}>{type}</li>
        ))}
      </ul>
    </section>
  )
}
