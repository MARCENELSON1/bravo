import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { useAuth } from "@/auth/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCreateOrder } from "@/hooks/use-orders"
import { useCreateTable, useTables } from "@/hooks/use-tables"

export function FloorPage() {
  const tables = useTables()
  const createOrder = useCreateOrder()
  const createTable = useCreateTable()
  const navigate = useNavigate()
  const { session } = useAuth()
  const canManage = session?.role === "OWNER" || session?.role === "MANAGER"
  const [newNumber, setNewNumber] = useState("")

  const openOrder = (tableId: string) => {
    createOrder.mutate(tableId, {
      onSuccess: (res) => navigate(`/app/orders/${res.order_id}`),
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos abrir la comanda."),
    })
  }

  const addTable = () => {
    const n = Number(newNumber)
    if (!Number.isInteger(n) || n <= 0) {
      toast.error("Número de mesa inválido.")
      return
    }
    createTable.mutate(
      { number: n, name: null },
      {
        onSuccess: () => {
          toast.success("Mesa agregada.")
          setNewNumber("")
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos agregar la mesa."),
      }
    )
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-2xl flex-col gap-4 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-medium">Mesas</h1>
        <Link to="/app" className="text-sm text-muted-foreground underline underline-offset-4">
          Volver
        </Link>
      </div>

      {canManage ? (
        <div className="flex items-end gap-2">
          <Input
            type="number"
            inputMode="numeric"
            placeholder="N° de mesa"
            value={newNumber}
            onChange={(e) => setNewNumber(e.target.value)}
            className="max-w-[8rem]"
          />
          <Button variant="outline" onClick={addTable} disabled={createTable.isPending}>
            Agregar mesa
          </Button>
        </div>
      ) : null}

      {tables.isPending ? (
        <Spinner />
      ) : tables.data && tables.data.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {tables.data.map((t) => (
            <Card
              key={t.id}
              className="cursor-pointer transition-colors hover:bg-muted/50"
              onClick={() => openOrder(t.id)}
            >
              <CardContent className="flex flex-col items-center justify-center gap-1 py-6">
                <span className="font-heading text-2xl font-medium">{t.number}</span>
                {t.name ? <span className="text-xs text-muted-foreground">{t.name}</span> : null}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          No hay mesas todavía{canManage ? " — agregá una arriba." : "."}
        </p>
      )}
    </div>
  )
}
