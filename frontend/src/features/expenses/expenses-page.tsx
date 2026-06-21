import { useState } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { PaymentMethod } from "@/api/types-operations"
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
import { useExpenses, useRegisterExpense } from "@/hooks/use-payments"
import { formatMoney } from "@/lib/money"

const EXPENSE_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: "CASH", label: "Efectivo" },
  { value: "TRANSFER", label: "Transferencia" },
  { value: "CARD", label: "Tarjeta" },
  { value: "MERCADOPAGO", label: "MercadoPago" },
]

export function ExpensesPage() {
  const expenses = useExpenses()
  const registerExpense = useRegisterExpense()
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [amount, setAmount] = useState("")
  const [category, setCategory] = useState("")
  const [counterparty, setCounterparty] = useState("")
  const [description, setDescription] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount) * 100)
    if (!Number.isFinite(minor) || minor < 1) {
      toast.error("Ingresá un monto válido.")
      return
    }
    registerExpense.mutate(
      {
        method,
        amount: minor,
        category: category.trim() || null,
        counterparty: counterparty.trim() || null,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Egreso registrado.")
          setAmount("")
          setCategory("")
          setCounterparty("")
          setDescription("")
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar el egreso."),
      }
    )
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-xl flex-col gap-4 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-medium">Egresos</h1>
        <Link to="/app" className="text-sm text-muted-foreground underline underline-offset-4">
          Volver
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Registrar egreso</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-end gap-2">
            <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)}>
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPENSE_METHODS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="number"
              min={0}
              step="0.01"
              placeholder="Monto"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="max-w-[8rem]"
            />
          </div>
          <Input
            placeholder="Rubro (p. ej. Proveedores)"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
          <Input
            placeholder="Contraparte (p. ej. Frigorífico Sur)"
            value={counterparty}
            onChange={(e) => setCounterparty(e.target.value)}
          />
          <Input
            placeholder="Descripción (opcional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button onClick={submit} disabled={registerExpense.isPending}>
            {registerExpense.isPending ? "Registrando…" : "Registrar egreso"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Últimos egresos</CardTitle>
        </CardHeader>
        <CardContent>
          {expenses.isPending ? (
            <Spinner className="size-5 text-muted-foreground" />
          ) : expenses.data && expenses.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border text-sm">
              {expenses.data.map((e) => (
                <li key={e.id} className="flex items-center justify-between gap-3 py-2">
                  <span className="flex flex-col">
                    <span className="font-medium">{e.counterparty ?? e.category ?? "Egreso"}</span>
                    <span className="text-xs text-muted-foreground">
                      {e.category ?? "—"}
                      {e.description ? ` · ${e.description}` : ""}
                    </span>
                  </span>
                  <span className="font-medium">{formatMoney(e.amount, e.currency)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Todavía no registraste egresos.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
