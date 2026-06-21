import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { PaymentMethod } from "@/api/types-operations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useExpenses, useRegisterExpense } from "@/hooks/use-payments"
import { formatMoney } from "@/lib/money"

const EXPENSE_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: "CASH", label: "Efectivo" },
  { value: "TRANSFER", label: "Transferencia" },
  { value: "CARD", label: "Tarjeta" },
  { value: "MERCADOPAGO", label: "MercadoPago" },
]

const methodLabel = (m: string) => EXPENSE_METHODS.find((x) => x.value === m)?.label ?? m

export function ExpensesPage() {
  const expenses = useExpenses()
  const registerExpense = useRegisterExpense()
  const [open, setOpen] = useState(false)
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
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar el egreso."),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-8">
      <header className="flex items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Egresos
          </GradientHeading>
          <p className="text-sm text-muted-foreground">Registrá y seguí las salidas de plata.</p>
        </div>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button>Nuevo egreso</Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Nuevo egreso</SheetTitle>
              <SheetDescription>Una salida de plata (proveedor, gasto, etc.).</SheetDescription>
            </SheetHeader>
            <div className="flex flex-col gap-3 px-4 pb-4">
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
            </div>
          </SheetContent>
        </Sheet>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {expenses.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : expenses.data && expenses.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contraparte</TableHead>
                <TableHead>Rubro</TableHead>
                <TableHead>Medio</TableHead>
                <TableHead className="text-right">Monto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {expenses.data.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="font-medium">
                    {e.counterparty ?? "—"}
                    {e.description ? (
                      <span className="block text-xs font-normal text-muted-foreground">
                        {e.description}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{e.category ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{methodLabel(e.method)}</Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(e.amount, e.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Todavía no registraste egresos.
          </p>
        )}
      </div>
    </div>
  )
}
