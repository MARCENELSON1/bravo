import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { OrderAction } from "@/api/orders-api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useKdsOrders } from "@/hooks/use-kds-orders"
import { useAdvanceOrder } from "@/hooks/use-orders"
import { useTables } from "@/hooks/use-tables"

export function KdsPage() {
  const kds = useKdsOrders()
  const tables = useTables()
  const advance = useAdvanceOrder()

  const tableNumber = (tableId: string): string => {
    const found = tables.data?.find((t) => t.id === tableId)
    return found ? String(found.number) : "—"
  }

  const advanceTo = (orderId: string, action: OrderAction) => {
    advance.mutate(
      { orderId, action },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No se pudo actualizar la comanda."),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Cocina (KDS)
        </GradientHeading>
        <p className="text-sm text-muted-foreground">Comandas en preparación, en vivo.</p>
      </header>

      {kds.isPending ? (
        <Spinner />
      ) : kds.data && kds.data.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {kds.data.map((o) => (
            <Card key={o.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Mesa {tableNumber(o.table_id)}</span>
                  <span className="text-xs font-normal text-muted-foreground">{o.status}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <ul className="flex flex-col gap-1 text-sm">
                  {o.items.map((it) => (
                    <li key={it.id}>
                      {it.quantity}× {it.name}
                      {it.note ? (
                        <span className="text-muted-foreground"> ({it.note})</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
                {o.status === "SENT" ? (
                  <Button size="sm" variant="outline" onClick={() => advanceTo(o.id, "preparing")}>
                    Empezar a preparar
                  </Button>
                ) : (
                  <Button size="sm" onClick={() => advanceTo(o.id, "ready")}>
                    Marcar listo
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No hay comandas en cocina.</p>
      )}
    </div>
  )
}
