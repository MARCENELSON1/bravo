import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { useAddItem, useOrder, useSendOrder } from "@/hooks/use-orders"
import { useProducts } from "@/hooks/use-products"
import { formatMoney } from "@/lib/money"

export function OrderPage() {
  const { orderId = "" } = useParams()
  const order = useOrder(orderId)
  const products = useProducts()
  const addItem = useAddItem(orderId)
  const sendOrder = useSendOrder()
  const navigate = useNavigate()
  const [productId, setProductId] = useState("")
  const [quantity, setQuantity] = useState("1")

  if (order.isPending) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <Spinner className="size-6 text-muted-foreground" />
      </div>
    )
  }

  if (order.isError || !order.data) {
    return (
      <div className="mx-auto max-w-md p-10 text-center text-sm text-muted-foreground">
        No encontramos la comanda.{" "}
        <Link to="/app/floor" className="underline underline-offset-4">
          Volver
        </Link>
      </div>
    )
  }

  const data = order.data
  const isOpen = data.status === "OPEN"

  const add = () => {
    if (!productId) {
      toast.error("Elegí un producto.")
      return
    }
    const q = Number(quantity)
    if (!Number.isInteger(q) || q < 1) {
      toast.error("Cantidad inválida.")
      return
    }
    addItem.mutate(
      { productId, quantity: q, note: null },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos agregar el ítem."),
      }
    )
  }

  const send = () => {
    sendOrder.mutate(orderId, {
      onSuccess: () => {
        toast.success("Comanda enviada a cocina.")
        navigate("/app/floor")
      },
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos enviar la comanda."),
    })
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-xl flex-col gap-4 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-medium">Comanda</h1>
        <Link to="/app/floor" className="text-sm text-muted-foreground underline underline-offset-4">
          Volver
        </Link>
      </div>

      {isOpen ? (
        <Card>
          <CardHeader>
            <CardTitle>Agregar ítem</CardTitle>
          </CardHeader>
          <CardContent className="flex items-end gap-2">
            <Select value={productId} onValueChange={setProductId}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Elegí un producto" />
              </SelectTrigger>
              <SelectContent>
                {(products.data ?? [])
                  .filter((p) => p.active)
                  .map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} · {formatMoney(p.price_amount, p.currency)}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <Input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="max-w-[5rem]"
            />
            <Button variant="outline" onClick={add} disabled={addItem.isPending}>
              Agregar
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Ítems · {data.status}</CardTitle>
        </CardHeader>
        <CardContent>
          {data.items.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {data.items.map((it) => (
                <li key={it.id} className="flex items-center justify-between py-2 text-sm">
                  <span>
                    {it.quantity}× {it.name}
                  </span>
                  <span className="font-medium">
                    {formatMoney(it.unit_price_amount * it.quantity, data.currency)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Sin ítems todavía.</p>
          )}
          <div className="mt-3 flex items-center justify-between border-t pt-3 text-sm font-medium">
            <span>Total</span>
            <span>{formatMoney(data.total_amount, data.currency)}</span>
          </div>
        </CardContent>
      </Card>

      {isOpen ? (
        <Button onClick={send} disabled={sendOrder.isPending || data.items.length === 0}>
          {sendOrder.isPending ? "Enviando…" : "Enviar a cocina"}
        </Button>
      ) : null}
    </div>
  )
}
