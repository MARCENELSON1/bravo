import { useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Spinner } from "@/components/ui/spinner"
import {
  classifyCustomers,
  coverage,
  type CustomerSegment,
} from "@/features/crm/customer-segments"
import { useCustomerStats } from "@/hooks/use-customers"
import { formatMoney } from "@/lib/money"
import { waLink } from "@/lib/wa"

// Orden por accionabilidad (lo que exige contacto primero). "sin_compras" y
// "ocasional" no son acciones → no tienen chip (pero cuentan en cobertura).
const SEGMENTS: { key: CustomerSegment; label: string; dot: string }[] = [
  { key: "en_riesgo", label: "En riesgo", dot: "bg-orange-500" },
  { key: "vip", label: "VIP", dot: "bg-violet-500" },
  { key: "nuevo", label: "Nuevos", dot: "bg-emerald-500" },
  { key: "recurrente", label: "Recurrentes", dot: "bg-sky-500" },
  { key: "ocasional", label: "Ocasionales", dot: "bg-neutral-400" },
]

export function CustomerSegmentsView() {
  const stats = useCustomerStats()
  const [selected, setSelected] = useState<CustomerSegment | null>(null)
  // "Ahora" congelado al montar (Date.now es impuro; una sola lectura estable).
  const [nowMs] = useState(() => Date.now())
  const rows = useMemo(() => stats.data?.rows ?? [], [stats.data])
  const currency = stats.data?.currency ?? "ARS"

  const classified = useMemo(() => classifyCustomers(rows, nowMs), [rows, nowMs])
  const cov = useMemo(() => coverage(rows), [rows])

  const counts = useMemo(() => {
    const m = new Map<CustomerSegment, number>()
    for (const c of classified) m.set(c.segment, (m.get(c.segment) ?? 0) + 1)
    return m
  }, [classified])

  if (stats.isPending) return <Spinner />
  if (rows.length === 0) return null

  const list = selected ? classified.filter((c) => c.segment === selected) : []

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <div>
        <h2 className="text-base font-semibold text-foreground">Segmentos</h2>
        <p className="text-sm text-muted-foreground">
          Segmentamos <span className="font-medium">{cov.withPurchases}</span> de {cov.total}{" "}
          clientes (los que tienen compras registradas). Atribuí clientes a las comandas para
          que entren más.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {SEGMENTS.map((s) => {
          const n = counts.get(s.key) ?? 0
          return (
            <Button
              key={s.key}
              size="sm"
              variant={selected === s.key ? "default" : "outline"}
              disabled={n === 0}
              onClick={() => setSelected((v) => (v === s.key ? null : s.key))}
            >
              <span className={`mr-1.5 inline-block size-2 rounded-full ${s.dot}`} />
              {s.label} · {n}
            </Button>
          )
        })}
      </div>

      {selected && list.length > 0 ? (
        <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {list.map((c) => {
            const link = waLink(c.phone, `Hola ${c.name}!`)
            return (
              <div key={c.customer_id} className="flex flex-wrap items-center gap-2 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium">{c.name}</span>
                  <p className="text-xs text-muted-foreground">
                    {c.visits} {c.visits === 1 ? "visita" : "visitas"} ·{" "}
                    {formatMoney(c.total_spent, currency)}
                    {c.daysSinceLast !== null ? ` · hace ${c.daysSinceLast}d` : ""}
                  </p>
                </div>
                {link ? (
                  <a href={link} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline">
                      WhatsApp
                    </Button>
                  </a>
                ) : null}
              </div>
            )
          })}
        </div>
      ) : null}
    </GlassCard>
  )
}
