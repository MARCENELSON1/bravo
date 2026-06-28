import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { DocType } from "@/api/types-invoicing"
import type { OrderDTO, PaymentMethod, ProductDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { ProductGrid } from "@/features/orders/product-grid"
import { useFloor } from "@/hooks/use-floor"
import { useIssueInvoice, useOrderInvoice } from "@/hooks/use-invoices"
import {
  useAddItem,
  useMergeOrders,
  useOrder,
  useRemoveItem,
  useSendOrder,
  useSetItemQuantity,
  useTransferOrder,
} from "@/hooks/use-orders"
import { useOrderPayments, useRegisterPayment } from "@/hooks/use-payments"
import { useProducts } from "@/hooks/use-products"
import { useTables } from "@/hooks/use-tables"
import {
  DOC_TYPE_LABELS,
  INVOICE_STATUS_LABELS,
  invoiceNumber,
  invoiceTypeLabel,
} from "@/lib/invoice-labels"
import { presetAmounts, sumLineItems } from "@/lib/cobro"
import { newId } from "@/lib/ids"
import { formatMoney } from "@/lib/money"
import { bumpUsage } from "@/lib/product-usage"
import { printTicket, ticketHtml } from "@/lib/ticket"

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: "CASH", label: "Efectivo" },
  { value: "CARD", label: "Tarjeta" },
  { value: "TRANSFER", label: "Transferencia" },
  { value: "MERCADOPAGO", label: "MercadoPago (link/QR)" },
  { value: "QR", label: "QR" },
]
const CHARGE_ROLES = ["CASHIER", "MANAGER", "OWNER"]
const EDIT_ROLES = ["WAITER", "MANAGER", "OWNER"]
const INVOICE_ROLES = ["OWNER", "MANAGER"]

export function OrderPage() {
  const { orderId = "" } = useParams()
  const { session } = useAuth()
  const role = session?.role ?? ""
  const canCharge = CHARGE_ROLES.includes(role)
  const canEdit = EDIT_ROLES.includes(role)
  const canInvoice = INVOICE_ROLES.includes(role)

  // While an online charge is pending we poll the order until the webhook flips
  // it to PAID.
  const [awaitingOnline, setAwaitingOnline] = useState(false)
  // While waiting for the webhook, poll until the order flips to PAID (the
  // function form reads the latest data, so polling stops on its own).
  const order = useOrder(orderId, {
    refetchInterval: awaitingOnline
      ? (query) => (query.state.data?.status === "PAID" ? false : 3000)
      : false,
  })
  const products = useProducts()
  const tables = useTables()
  const addItem = useAddItem(orderId)
  const removeItem = useRemoveItem(orderId)
  const setItemQty = useSetItemQuantity(orderId)
  const sendOrder = useSendOrder()
  const navigate = useNavigate()

  const isPaid = order.data?.status === "PAID"
  useEffect(() => {
    // Fires once when the webhook flips the order to PAID while we were waiting.
    if (isPaid && awaitingOnline) {
      toast.success("¡Cobro confirmado! La comanda quedó pagada.")
    }
  }, [isPaid, awaitingOnline])

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
  // Rounds: items can be added/marched while the order is in service, not just
  // when it's OPEN. Only a PAID/CANCELLED order is closed to new items.
  const canAddRound = canEdit && !isPaid && data.status !== "CANCELLED"
  const pendingCount = data.items.filter((it) => it.status === "PENDING").length

  const handleAdd = (product: ProductDTO, quantity: number) => {
    bumpUsage(product.id) // learn favorites for the grid ranking
    addItem.mutate(
      {
        id: newId(),
        productId: product.id,
        name: product.name,
        unitPriceAmount: product.price_amount,
        quantity,
        note: null,
        station: product.station,
      },
      {
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos agregar el ítem."),
      }
    )
  }

  const send = () => {
    sendOrder.mutate(orderId, {
      onSuccess: () => {
        toast.success("Ítems marchados a su estación.")
        navigate("/app/floor")
      },
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos marchar la comanda."),
    })
  }

  const printComanda = () => {
    const number = tables.data?.find((t) => t.id === data.table_id)?.number
    const label = number != null ? `Mesa ${number}` : "Comanda"
    const printedAt = new Date().toLocaleString("es-AR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
    printTicket(ticketHtml(data, label, printedAt))
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 px-6 py-8">
      <header className="flex items-center justify-between gap-2">
        <GradientHeading size="md" weight="bold">
          Comanda
        </GradientHeading>
        <Link
          to="/app/floor"
          className="text-sm text-muted-foreground underline underline-offset-4"
        >
          ← Mesas
        </Link>
      </header>

      {canAddRound ? (
        <Card>
          <CardHeader>
            <CardTitle>{data.status === "OPEN" ? "Agregar ítem" : "Agregar otra ronda"}</CardTitle>
          </CardHeader>
          <CardContent>
            <ProductGrid products={products.data ?? []} onAdd={handleAdd} />
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2">
            <span>Ítems · {data.status}</span>
            {canEdit && data.items.length > 0 ? (
              <Button variant="outline" size="sm" onClick={printComanda}>
                Imprimir
              </Button>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.items.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {data.items.map((it) => (
                <li key={it.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <span className="flex-1">
                    {it.quantity}× {it.name}
                    {it.note ? (
                      <span className="text-muted-foreground"> ({it.note})</span>
                    ) : null}
                    {it.status !== "PENDING" ? (
                      <span className="ml-1 text-xs text-muted-foreground">· {it.status}</span>
                    ) : null}
                  </span>
                  {it.status === "PENDING" && canEdit ? (
                    <span className="flex items-center gap-1">
                      <Button
                        variant="outline"
                        className="h-8 w-8 p-0 text-base"
                        onClick={() =>
                          setItemQty.mutate({
                            itemId: it.id,
                            quantity: Math.max(1, it.quantity - 1),
                          })
                        }
                      >
                        −
                      </Button>
                      <Button
                        variant="outline"
                        className="h-8 w-8 p-0 text-base"
                        onClick={() =>
                          setItemQty.mutate({ itemId: it.id, quantity: it.quantity + 1 })
                        }
                      >
                        +
                      </Button>
                      <Button
                        variant="ghost"
                        className="h-8 w-8 p-0 text-destructive"
                        onClick={() =>
                          removeItem.mutate(it.id, {
                            onError: (error) =>
                              toast.error(
                                isApiError(error)
                                  ? error.message
                                  : "No pudimos quitar el ítem."
                              ),
                          })
                        }
                      >
                        ✕
                      </Button>
                    </span>
                  ) : null}
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

      {canAddRound ? (
        <Button onClick={send} disabled={sendOrder.isPending || pendingCount === 0}>
          {sendOrder.isPending ? "Marchando…" : `Marchar${pendingCount > 0 ? ` (${pendingCount})` : ""}`}
        </Button>
      ) : null}

      {canAddRound ? <TableMoveSection order={data} /> : null}

      {canCharge && data.status !== "CANCELLED" ? (
        <CobroSection order={data} onPendingOnline={() => setAwaitingOnline(true)} />
      ) : null}

      {canInvoice && data.status === "PAID" ? <FacturaSection order={data} /> : null}
    </div>
  )
}

// Move this order to a free table, or join another occupied table into it. Both
// read the live floor so the cashier/waiter picks a real target.
function TableMoveSection({ order }: { order: OrderDTO }) {
  const floor = useFloor()
  const transfer = useTransferOrder(order.id)
  const merge = useMergeOrders(order.id)
  const [moveTo, setMoveTo] = useState("")
  const [mergeFrom, setMergeFrom] = useState("")

  const tables = floor.data ?? []
  const freeTables = tables.filter((t) => !t.active_order && t.id !== order.table_id)
  const otherOccupied = tables.filter(
    (t) => t.active_order && t.active_order.id !== order.id
  )

  const doMove = () => {
    if (!moveTo) return
    transfer.mutate(moveTo, {
      onSuccess: () => {
        toast.success("Mesa cambiada.")
        setMoveTo("")
      },
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos mover la mesa."),
    })
  }

  const doMerge = () => {
    if (!mergeFrom) return
    merge.mutate(mergeFrom, {
      onSuccess: () => {
        toast.success("Mesas unidas.")
        setMergeFrom("")
      },
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos unir las mesas."),
    })
  }

  const selectClass =
    "h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mesa</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <select
            className={selectClass}
            value={moveTo}
            onChange={(e) => setMoveTo(e.target.value)}
            aria-label="Mover a mesa libre"
          >
            <option value="">Mover a mesa…</option>
            {freeTables.map((t) => (
              <option key={t.id} value={t.id}>
                Mesa {t.number}
                {t.name ? ` (${t.name})` : ""}
              </option>
            ))}
          </select>
          <Button variant="outline" onClick={doMove} disabled={!moveTo || transfer.isPending}>
            Mover
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <select
            className={selectClass}
            value={mergeFrom}
            onChange={(e) => setMergeFrom(e.target.value)}
            aria-label="Unir otra mesa acá"
          >
            <option value="">Unir otra mesa acá…</option>
            {otherOccupied.map((t) => (
              <option key={t.id} value={t.active_order!.id}>
                Mesa {t.number}
                {t.name ? ` (${t.name})` : ""}
              </option>
            ))}
          </select>
          <Button variant="outline" onClick={doMerge} disabled={!mergeFrom || merge.isPending}>
            Unir
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Unir trae los ítems de la otra mesa a esta y libera la de origen.
        </p>
      </CardContent>
    </Card>
  )
}

const INVOICE_DOC_TYPES: { value: DocType; label: string }[] = [
  { value: "CONSUMIDOR_FINAL", label: DOC_TYPE_LABELS.CONSUMIDOR_FINAL },
  { value: "CUIT", label: DOC_TYPE_LABELS.CUIT },
  { value: "DNI", label: DOC_TYPE_LABELS.DNI },
]

// Shown on a paid comanda (OWNER/MANAGER): emits the AFIP comprobante or, if one
// already exists, shows its CAE. The A/B/C type is derived server-side.
function FacturaSection({ order }: { order: OrderDTO }) {
  const invoice = useOrderInvoice(order.id)
  const issue = useIssueInvoice(order.id)
  const [docType, setDocType] = useState<DocType>("CONSUMIDOR_FINAL")
  const [docNumber, setDocNumber] = useState("")

  const emitir = () => {
    const needsDoc = docType !== "CONSUMIDOR_FINAL"
    const number = needsDoc ? docNumber.trim() : "0"
    if (needsDoc && !/^\d{7,11}$/.test(number)) {
      toast.error("Ingresá un CUIT/DNI válido (solo números).")
      return
    }
    issue.mutate(
      { doc_type: docType, doc_number: number },
      {
        onSuccess: (inv) => {
          if (inv.status === "AUTHORIZED") toast.success(`Factura autorizada · CAE ${inv.cae}`)
          else
            toast.error(
              `AFIP rechazó el comprobante${inv.rejection ? `: ${inv.rejection}` : "."}`
            )
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos emitir la factura."),
      }
    )
  }

  if (invoice.isPending) {
    return (
      <Card>
        <CardContent className="flex justify-center py-6">
          <Spinner className="size-5 text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  const existing = invoice.data
  if (existing && existing.status === "AUTHORIZED") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Facturación</span>
            <Badge>{INVOICE_STATUS_LABELS.AUTHORIZED}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">{invoiceTypeLabel(existing.type)}</span>
            <span className="font-medium tabular-nums">
              {invoiceNumber(existing.point_of_sale, existing.number)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">CAE</span>
            <span className="font-mono text-xs">{existing.cae}</span>
          </div>
          {existing.cae_expiration ? (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Vencimiento CAE</span>
              <span>{existing.cae_expiration}</span>
            </div>
          ) : null}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Facturar</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {existing && existing.status === "REJECTED" ? (
          <p className="rounded-md border border-destructive/40 bg-destructive/5 p-2 text-xs text-destructive">
            AFIP rechazó el último intento
            {existing.rejection ? `: ${existing.rejection}` : "."} Probá de nuevo.
          </p>
        ) : null}
        <div className="flex items-end gap-2">
          <Select value={docType} onValueChange={(v) => setDocType(v as DocType)}>
            <SelectTrigger className="flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INVOICE_DOC_TYPES.map((d) => (
                <SelectItem key={d.value} value={d.value}>
                  {d.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {docType !== "CONSUMIDOR_FINAL" ? (
            <Input
              inputMode="numeric"
              placeholder={docType === "CUIT" ? "CUIT" : "DNI"}
              value={docNumber}
              onChange={(e) => setDocNumber(e.target.value)}
              className="max-w-[10rem]"
            />
          ) : null}
        </div>
        <Button onClick={emitir} disabled={issue.isPending}>
          {issue.isPending ? "Emitiendo…" : "Emitir factura"}
        </Button>
        <p className="text-xs text-muted-foreground">
          Necesitás AFIP conectado en Integraciones. El tipo (A/B/C) se determina solo.
        </p>
      </CardContent>
    </Card>
  )
}

function CobroSection({
  order,
  onPendingOnline,
}: {
  order: OrderDTO
  onPendingOnline: () => void
}) {
  const payments = useOrderPayments(order.id)
  const registerPayment = useRegisterPayment(order.id)
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [amount, setAmount] = useState("")
  const [splitMode, setSplitMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null)

  const list = payments.data ?? []
  const confirmed = list
    .filter((p) => p.direction === "INFLOW" && p.status === "CONFIRMED")
    .reduce((sum, p) => sum + p.amount, 0)
  const remaining = Math.max(order.total_amount - confirmed, 0)
  const isPaid = order.status === "PAID"
  const splitAmount = sumLineItems(order.items, selected)

  // What the cashier types is in pesos; the API works in minor units. In split
  // mode the amount comes from the selected items instead.
  const computeCharge = (): number => {
    if (splitMode) return splitAmount
    if (amount.trim()) return Math.round(Number(amount) * 100)
    return remaining
  }

  const toggleItem = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const cobrar = () => {
    const minor = computeCharge()
    if (!Number.isFinite(minor) || minor < 1) {
      toast.error("Ingresá un monto válido.")
      return
    }
    setCheckoutUrl(null)
    registerPayment.mutate(
      { method, amount: minor },
      {
        onSuccess: (payment) => {
          setAmount("")
          setSelected(new Set())
          setSplitMode(false)
          if (payment.status === "PENDING" && payment.checkout_url) {
            setCheckoutUrl(payment.checkout_url)
            onPendingOnline()
            toast.info("Generamos el link de pago. Compartilo o que escaneen el QR.")
          } else {
            toast.success("Cobro registrado.")
          }
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar el cobro."),
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Cobrar</span>
          {isPaid ? (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              Pagada
            </span>
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {list.length > 0 ? (
          <ul className="flex flex-col divide-y divide-border text-sm">
            {list.map((p) => (
              <li key={p.id} className="flex items-center justify-between py-1.5">
                <span className="text-muted-foreground">
                  {PAYMENT_METHODS.find((m) => m.value === p.method)?.label ?? p.method}
                </span>
                <span className="flex items-center gap-2">
                  {formatMoney(p.amount, p.currency)}
                  <span
                    className={
                      p.status === "CONFIRMED"
                        ? "text-xs text-emerald-600"
                        : "text-xs text-amber-600"
                    }
                  >
                    {p.status === "CONFIRMED" ? "confirmado" : "pendiente"}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        ) : null}

        {!isPaid ? (
          <div className="flex items-center justify-between text-sm font-medium">
            <span>Restante</span>
            <span>{formatMoney(remaining, order.currency)}</span>
          </div>
        ) : null}

        {!isPaid ? (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              {PAYMENT_METHODS.map((m) => (
                <Button
                  key={m.value}
                  type="button"
                  size="sm"
                  variant={method === m.value ? "default" : "outline"}
                  onClick={() => setMethod(m.value)}
                >
                  {m.label}
                </Button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setSplitMode((s) => !s)}
              className="self-start text-xs text-muted-foreground underline underline-offset-4"
            >
              {splitMode ? "← Cobrar un monto" : "Dividir por ítem"}
            </button>

            {splitMode ? (
              <div className="flex flex-col gap-1 rounded-md border p-2 text-sm">
                {order.items.map((it) => (
                  <label key={it.id} className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selected.has(it.id)}
                        onChange={() => toggleItem(it.id)}
                      />
                      {it.quantity}× {it.name}
                    </span>
                    <span>{formatMoney(it.unit_price_amount * it.quantity, order.currency)}</span>
                  </label>
                ))}
                <div className="mt-1 flex justify-between border-t pt-1 font-medium">
                  <span>Seleccionado</span>
                  <span>{formatMoney(splitAmount, order.currency)}</span>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                <Input
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder={(remaining / 100).toFixed(2)}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="max-w-[8rem]"
                />
                {presetAmounts(remaining).map((p) => (
                  <Button
                    key={p.label}
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setAmount((p.amount / 100).toFixed(2))}
                  >
                    {p.label}
                  </Button>
                ))}
              </div>
            )}

            <Button
              onClick={cobrar}
              disabled={registerPayment.isPending || (splitMode && splitAmount < 1)}
            >
              {registerPayment.isPending
                ? "…"
                : `Cobrar ${formatMoney(computeCharge(), order.currency)}`}
            </Button>
          </div>
        ) : null}

        {checkoutUrl && !isPaid ? (
          <div className="flex flex-col gap-2 rounded-md border border-dashed p-3 text-sm">
            <p className="text-muted-foreground">
              Pago online generado. Esperando confirmación de MercadoPago…
            </p>
            <Button asChild variant="outline">
              <a href={checkoutUrl} target="_blank" rel="noreferrer">
                Abrir checkout / QR
              </a>
            </Button>
            <Spinner className="size-4 self-center text-muted-foreground" />
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
