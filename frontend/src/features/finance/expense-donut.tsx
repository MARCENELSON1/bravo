import { useTranslation } from "react-i18next"

import type { ExpenseCategoryRowDTO } from "@/api/types-operations"
import { GlassCard } from "@/components/ui/glass-card"
import { formatMoney } from "@/lib/money"

// Paleta de la marca (verdes) + neutros para el resto. ≤5 categorías + "Otros".
const COLORS = ["#3fb37f", "#2f8f68", "#7cc9a4", "#b7936a", "#8a9d94", "#5c7a6e"]
const RADIUS = 52
const CIRC = 2 * Math.PI * RADIUS

// Agrupa a top 5 + "Otros" para no ensuciar el donut.
function topWithRest(
  rows: ExpenseCategoryRowDTO[],
  otherLabel: string,
): { category: string; amount: number }[] {
  const sorted = [...rows].filter((r) => r.amount > 0).sort((a, b) => b.amount - a.amount)
  if (sorted.length <= 6) return sorted.map((r) => ({ category: r.category, amount: r.amount }))
  const top = sorted.slice(0, 5).map((r) => ({ category: r.category, amount: r.amount }))
  const rest = sorted.slice(5).reduce((s, r) => s + r.amount, 0)
  return [...top, { category: otherLabel, amount: rest }]
}

export function ExpenseDonut({
  rows,
  total,
  currency,
  selected,
  onSelect,
}: {
  rows: ExpenseCategoryRowDTO[]
  total: number
  currency: string
  selected: string | null
  onSelect: (category: string | null) => void
}) {
  const { t } = useTranslation()
  const segments = topWithRest(rows, t("finance.expenseDonut.other"))

  return (
    <GlassCard className="p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        {t("finance.expenseDonut.title")}
      </h2>
      {total <= 0 ? (
        <p className="text-sm text-muted-foreground">{t("finance.expenseDonut.empty")}</p>
      ) : (
        <div className="flex flex-wrap items-center gap-6">
          <svg viewBox="0 0 140 140" className="size-40 shrink-0 -rotate-90">
            {segments.reduce<{ offset: number; nodes: React.ReactNode[] }>(
              (acc, seg, i) => {
                const frac = seg.amount / total
                const len = frac * CIRC
                const dim = selected && selected !== seg.category
                acc.nodes.push(
                  <circle
                    key={seg.category}
                    cx="70"
                    cy="70"
                    r={RADIUS}
                    fill="none"
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth="16"
                    strokeDasharray={`${len} ${CIRC - len}`}
                    strokeDashoffset={-acc.offset}
                    opacity={dim ? 0.3 : 1}
                    className="cursor-pointer transition-opacity"
                    onClick={() => onSelect(selected === seg.category ? null : seg.category)}
                  />
                )
                acc.offset += len
                return acc
              },
              { offset: 0, nodes: [] }
            ).nodes}
          </svg>
          <ul className="flex min-w-0 flex-1 flex-col gap-1.5 text-sm">
            {segments.map((seg, i) => {
              const share = Math.round((seg.amount / total) * 100)
              return (
                <li
                  key={seg.category}
                  className="flex cursor-pointer items-center gap-2"
                  onClick={() => onSelect(selected === seg.category ? null : seg.category)}
                >
                  <span
                    className="size-3 shrink-0 rounded-sm"
                    style={{ backgroundColor: COLORS[i % COLORS.length] }}
                  />
                  <span className="min-w-0 flex-1 truncate text-foreground">{seg.category}</span>
                  <span className="tabular-nums text-muted-foreground">
                    {formatMoney(seg.amount, currency)} · {share}%
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </GlassCard>
  )
}
