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

export function Audience() {
  const t = COPY[useContainer().locale]

  return (
    <section className="border-b border-border">
      <div className="mx-auto max-w-6xl px-5 py-10">
        <p className="text-center text-sm text-muted-foreground">{t.label}</p>
        <ul className="mt-4 flex flex-wrap items-center justify-center gap-x-3 gap-y-2">
          {t.types.map((type) => (
            <li
              key={type}
              className="rounded-full border border-border bg-card px-4 py-1.5 text-sm font-medium text-muted-foreground"
            >
              {type}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
