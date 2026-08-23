import { useMemo, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Spinner } from "@/components/ui/spinner"
import { todaysActions } from "@/features/crm/customer-segments"
import {
  useContactResult,
  useCustomers,
  useCustomerStats,
  useLogContact,
  useRecentContacts,
} from "@/hooks/use-customers"
import { formatMoney } from "@/lib/money"
import { waLink } from "@/lib/wa"

// El corazón del CRM: "acciones para hoy" (máx 3 en riesgo por plata en juego) +
// el loop de resultado arriba (contactaste N, volvieron M, $X).
export function CustomerActionsView() {
  const stats = useCustomerStats()
  const customers = useCustomers()
  const recent = useRecentContacts(7)
  const result = useContactResult(30)
  const logContact = useLogContact()
  const [nowMs] = useState(() => Date.now())

  const optOutIds = useMemo(
    () => new Set((customers.data ?? []).filter((c) => c.no_contactar).map((c) => c.id)),
    [customers.data]
  )
  const recentIds = useMemo(
    () => new Set(recent.data?.customer_ids ?? []),
    [recent.data]
  )
  const rows = useMemo(() => stats.data?.rows ?? [], [stats.data])
  const currency = stats.data?.currency ?? "ARS"
  const actions = useMemo(
    () => todaysActions(rows, optOutIds, recentIds, nowMs),
    [rows, optOutIds, recentIds, nowMs]
  )

  if (stats.isPending) return <Spinner />
  if (rows.length === 0) return null

  const res = result.data

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <div>
        <h2 className="text-base font-semibold text-foreground">Acciones para hoy</h2>
        {res && res.contacted > 0 ? (
          <p className="text-sm text-muted-foreground">
            En los últimos 30 días contactaste{" "}
            <span className="font-medium text-foreground">{res.contacted}</span>, volvieron{" "}
            <span className="font-medium text-foreground">{res.returned}</span> y gastaron{" "}
            <span className="font-medium text-foreground">
              {formatMoney(res.revenue, res.currency)}
            </span>
            .
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Clientes que venían seguido y dejaron de aparecer — los de mayor plata en juego.
          </p>
        )}
      </div>

      {actions.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nada urgente hoy. Atribuí clientes a las comandas para detectar a los que se
          enfrían.
        </p>
      ) : (
        <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {actions.map((c) => {
            const link = waLink(
              c.phone,
              `Hola ${c.name}! Te extrañamos, ¿te esperamos pronto?`
            )
            return (
              <div key={c.customer_id} className="flex flex-wrap items-center gap-2 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium">{c.name}</span>
                  <p className="text-xs text-muted-foreground">
                    En riesgo · {formatMoney(c.total_spent, currency)} gastados
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
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={logContact.isPending}
                  onClick={() =>
                    logContact.mutate(
                      { id: c.customer_id, reason: "en_riesgo" },
                      {
                        onSuccess: () => toast.success("Marcado como contactado."),
                        onError: (e) =>
                          toast.error(
                            isApiError(e) ? e.message : "No pudimos registrar el contacto."
                          ),
                      }
                    )
                  }
                >
                  Marcar contactado
                </Button>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}
