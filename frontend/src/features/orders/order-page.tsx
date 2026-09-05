import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { Link, useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { apiErrorText } from "@/api/translate-error"
import { dateLocale } from "@/lib/format"
import type { DocType } from "@/api/types-invoicing"
import type { Course, OrderDTO, PaymentMethod, ProductDTO } from "@/api/types-operations"
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
import { useCustomers } from "@/hooks/use-customers"
import { useFloor } from "@/hooks/use-floor"
import { useIssueInvoice, useOrderInvoice } from "@/hooks/use-invoices"
import {
  useAddItem,
  useAssignCustomer,
  useMergeOrders,
  useOrder,
  useRemoveItem,
  useReopenOrder,
  useAdvanceCourse,
  useFireAllCourses,
  useFireNextCourse,
  useSendOrder,
  useSetItemQuantity,
  useTransferOrder,
} from "@/hooks/use-orders"
import { useOrderPayments, useRefundPayment, useRegisterPayment } from "@/hooks/use-payments"
import { useOrderTaxQuote } from "@/hooks/use-tenant"
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
import { courseState, coursesOf, heldCount, itemsOfCourse, nextHeldCourse, readyCourse } from "@/lib/courses"
import { bumpUsage } from "@/lib/product-usage"
import { printTicket, receiptHtml, ticketHtml } from "@/lib/ticket"

// El label se resuelve en el consumidor con t(`orders.paymentMethods.${value}`);
// el código (CASH/CARD/…) es dato estable, no cambia por idioma.
const PAYMENT_METHODS: PaymentMethod[] = ["CASH", "CARD", "TRANSFER", "MERCADOPAGO", "QR"]
const CHARGE_ROLES = ["CASHIER", "MANAGER", "OWNER"]
const EDIT_ROLES = ["WAITER", "MANAGER", "OWNER"]
const INVOICE_ROLES = ["OWNER", "MANAGER"]

export function OrderPage() {
  const { t } = useTranslation()
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
  const fireNext = useFireNextCourse()
  const fireAll = useFireAllCourses()
  const advanceCourse = useAdvanceCourse()
  const navigate = useNavigate()

  const isPaid = order.data?.status === "PAID"
  useEffect(() => {
    // Fires once when the webhook flips the order to PAID while we were waiting.
    if (isPaid && awaitingOnline) {
      toast.success(t("orders.toasts.chargeConfirmed"))
    }
  }, [isPaid, awaitingOnline, t])

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
        {t("orders.notFound")}{" "}
        <Link to="/app/floor" className="underline underline-offset-4">
          {t("orders.backToFloor")}
        </Link>
      </div>
    )
  }

  const data = order.data
  // Rounds: items can be added/marched while the order is in service, not just
  // when it's OPEN. Only a PAID/CANCELLED order is closed to new items.
  const canAddRound = canEdit && !isPaid && data.status !== "CANCELLED"
  const pendingCount = data.items.filter((it) => it.status === "PENDING").length
  // Tiempos de servicio: qué toca ahora. Servir es SIEMPRE por curso (servir
  // "toda la orden" mezclaría la entrada lista con el principal recién salido).
  const courses = coursesOf(data.items)
  const nextCourse = nextHeldCourse(data)
  const courseToServe = readyCourse(data)
  const held = heldCount(data)
  const tableNumber = tables.data?.find((tbl) => tbl.id === data.table_id)?.number
  const tableLabel =
    tableNumber != null ? t("orders.table", { number: tableNumber }) : t("orders.orderFallback")

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
          toast.error(apiErrorText(error, t, t("orders.errors.addItemFailed"))),
      }
    )
  }

  const fireNextCourse = () => {
    fireNext.mutate(orderId, {
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.fireCourseFailed"))),
    })
  }

  const fireEverything = () => {
    fireAll.mutate(orderId, {
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.fireCourseFailed"))),
    })
  }

  const serveCourse = (course: Course) => {
    advanceCourse.mutate(
      { orderId, course, action: "served" },
      {
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("orders.errors.serveCourseFailed"))),
      }
    )
  }

  const send = () => {
    sendOrder.mutate(orderId, {
      onSuccess: () => {
        toast.success(t("orders.toasts.itemsMarched"))
        navigate("/app/floor")
      },
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.marchFailed"))),
    })
  }

  const printComanda = () => {
    const printedAt = new Date().toLocaleString(dateLocale(), {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
    printTicket(
      ticketHtml(data, tableLabel, printedAt, undefined, {
        stations: {
          KITCHEN: t("orders.ticket.stations.KITCHEN"),
          BAR: t("orders.ticket.stations.BAR"),
        },
        empty: t("orders.ticket.empty"),
      }),
      t("orders.ticket.windowTitle")
    )
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex items-center justify-between gap-2">
        <GradientHeading size="md" weight="bold">
          {t("orders.heading")}
        </GradientHeading>
        <Link
          to="/app/floor"
          className="text-sm text-muted-foreground underline underline-offset-4"
        >
          {t("orders.backToTables")}
        </Link>
      </header>

      <OrderCustomer order={data} />

      {canAddRound ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {data.status === "OPEN" ? t("orders.addItem") : t("orders.addRound")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ProductGrid products={products.data ?? []} onAdd={handleAdd} />
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              {t("orders.itemsTitle", { status: data.status })}
              {data.source === "CUSTOMER_QR" ? (
                <Badge variant="secondary">{t("orders.customerOrder")}</Badge>
              ) : null}
            </span>
            {canEdit && data.items.length > 0 ? (
              <Button variant="outline" size="sm" onClick={printComanda}>
                {t("orders.print")}
              </Button>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.items.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {courses.flatMap((course) => [
                // Cabecera del tiempo: su estado y la acción que le toca.
                <li key={`c-${course}`} className="flex items-center gap-2 pt-3 pb-1">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {t(`orders.courses.${course}`)}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {t(`orders.courseStates.${courseState(data.items, course) ?? "PENDING"}`)}
                  </span>
                  <span className="ml-auto">
                    {courseToServe === course ? (
                      <Button
                        variant="outline"
                        className="h-7 px-2 text-xs"
                        disabled={advanceCourse.isPending}
                        onClick={() => serveCourse(course)}
                      >
                        {t("orders.serveCourse", { course: t(`orders.courses.${course}`) })}
                      </Button>
                    ) : nextCourse === course && canAddRound ? (
                      <Button
                        variant="outline"
                        className="h-7 px-2 text-xs"
                        disabled={fireNext.isPending}
                        onClick={fireNextCourse}
                      >
                        {t("orders.fireCourse", { course: t(`orders.courses.${course}`) })}
                      </Button>
                    ) : null}
                  </span>
                </li>,
                ...itemsOfCourse(data.items, course).map((it) => (
                <li key={it.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <span className="flex-1">
                    {it.quantity}× {it.name}
                    {it.note ? (
                      <span className="text-muted-foreground"> ({it.note})</span>
                    ) : null}
                    {it.status === "READY" || it.status === "SERVED" ? (
                      <span className="ml-1 text-xs text-muted-foreground">
                        · {t(`orders.courseStates.${it.status}`)}
                      </span>
                    ) : null}
                    {it.selected_options && it.selected_options.length > 0 ? (
                      <span className="block text-xs text-muted-foreground">
                        {it.selected_options.map((o) => o.name).join(" · ")}
                      </span>
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
                                apiErrorText(error, t, t("orders.errors.removeItemFailed"))
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
                )),
              ])}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">{t("orders.noItems")}</p>
          )}
          {held > 0 ? (
            <p className="pt-2 text-xs text-muted-foreground">{t("orders.courseHint")}</p>
          ) : null}
          <OrderTotalBreakdown
            orderId={data.id}
            subtotal={data.total_amount}
            currency={data.currency}
          />
        </CardContent>
      </Card>

      {canAddRound ? (
        <div className="flex flex-col gap-2 sm:flex-row">
          {/* Lo que toca ahora: marchar lo cargado, o disparar el tiempo en espera. */}
          {pendingCount > 0 || nextCourse === null ? (
            <Button
              className="flex-1"
              onClick={send}
              disabled={sendOrder.isPending || pendingCount === 0}
            >
              {sendOrder.isPending
                ? t("orders.marching")
                : pendingCount > 0
                  ? t("orders.marchCount", { count: pendingCount })
                  : t("orders.march")}
            </Button>
          ) : (
            <Button className="flex-1" onClick={fireNextCourse} disabled={fireNext.isPending}>
              {t("orders.fireCourse", { course: t(`orders.courses.${nextCourse}`) })}
            </Button>
          )}
          {/* "Traé todo junto": solo si quedó algún tiempo en espera. */}
          {held > 0 ? (
            <Button variant="outline" onClick={fireEverything} disabled={fireAll.isPending}>
              {t("orders.fireAll")}
            </Button>
          ) : null}
        </div>
      ) : null}

      {canAddRound ? <TableMoveSection order={data} /> : null}

      {canCharge && data.status !== "CANCELLED" ? (
        <CobroSection
          order={data}
          tableLabel={tableLabel}
          onPendingOnline={() => setAwaitingOnline(true)}
        />
      ) : null}

      {canInvoice && data.status === "PAID" ? <FacturaSection order={data} /> : null}
    </div>
  )
}

// CRM: atribuir la comanda a un cliente para que sume a su historial de compras.
function OrderCustomer({ order }: { order: OrderDTO }) {
  const { t } = useTranslation()
  const customers = useCustomers()
  const assign = useAssignCustomer(order.id)
  const [search, setSearch] = useState("")

  const all = customers.data ?? []
  const current = order.customer_id ? all.find((c) => c.id === order.customer_id) : null
  const q = search.trim().toLowerCase()
  const matches = q
    ? all
        .filter(
          (c) => c.name.toLowerCase().includes(q) || (c.phone ?? "").includes(q)
        )
        .slice(0, 5)
    : []

  const set = (customerId: string | null) =>
    assign.mutate(customerId, {
      onSuccess: () => setSearch(""),
      onError: (e) =>
        toast.error(apiErrorText(e, t, t("orders.errors.customerAssignFailed"))),
    })

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("orders.customer")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {order.customer_id ? (
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm text-foreground">
              {current ? current.name : t("orders.customerAssigned")}
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive"
              disabled={assign.isPending}
              onClick={() => set(null)}
            >
              {t("orders.remove")}
            </Button>
          </div>
        ) : (
          <>
            <Input
              placeholder={t("orders.customerSearchPlaceholder")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {matches.length > 0 ? (
              <div className="flex flex-col divide-y divide-border rounded-md border border-border">
                {matches.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    disabled={assign.isPending}
                    onClick={() => set(c.id)}
                    className="flex items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent/50"
                  >
                    <span>{c.name}</span>
                    {c.phone ? (
                      <span className="text-xs text-muted-foreground">{c.phone}</span>
                    ) : null}
                  </button>
                ))}
              </div>
            ) : q ? (
              <p className="text-xs text-muted-foreground">{t("orders.noCustomers")}</p>
            ) : (
              <p className="text-xs text-muted-foreground">{t("orders.customerHint")}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

// Move this order to a free table, or join another occupied table into it. Both
// read the live floor so the cashier/waiter picks a real target.
function TableMoveSection({ order }: { order: OrderDTO }) {
  const { t } = useTranslation()
  const floor = useFloor()
  const transfer = useTransferOrder(order.id)
  const merge = useMergeOrders(order.id)
  const [moveTo, setMoveTo] = useState("")
  const [mergeFrom, setMergeFrom] = useState("")

  const tables = floor.data ?? []
  const freeTables = tables.filter((tbl) => !tbl.active_order && tbl.id !== order.table_id)
  const otherOccupied = tables.filter(
    (tbl) => tbl.active_order && tbl.active_order.id !== order.id
  )

  const doMove = () => {
    if (!moveTo) return
    transfer.mutate(moveTo, {
      onSuccess: () => {
        toast.success(t("orders.toasts.tableChanged"))
        setMoveTo("")
      },
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.moveFailed"))),
    })
  }

  const doMerge = () => {
    if (!mergeFrom) return
    merge.mutate(mergeFrom, {
      onSuccess: () => {
        toast.success(t("orders.toasts.tablesMerged"))
        setMergeFrom("")
      },
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.mergeFailed"))),
    })
  }

  const selectClass =
    "h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("orders.tableSection")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <select
            className={selectClass}
            value={moveTo}
            onChange={(e) => setMoveTo(e.target.value)}
            aria-label={t("orders.moveToFreeTable")}
          >
            <option value="">{t("orders.moveToTablePlaceholder")}</option>
            {freeTables.map((tbl) => (
              <option key={tbl.id} value={tbl.id}>
                {t("orders.table", { number: tbl.number })}
                {tbl.name ? ` (${tbl.name})` : ""}
              </option>
            ))}
          </select>
          <Button variant="outline" onClick={doMove} disabled={!moveTo || transfer.isPending}>
            {t("orders.move")}
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <select
            className={selectClass}
            value={mergeFrom}
            onChange={(e) => setMergeFrom(e.target.value)}
            aria-label={t("orders.mergeTableHere")}
          >
            <option value="">{t("orders.mergeTablePlaceholder")}</option>
            {otherOccupied.map((tbl) => (
              <option key={tbl.id} value={tbl.active_order!.id}>
                {t("orders.table", { number: tbl.number })}
                {tbl.name ? ` (${tbl.name})` : ""}
              </option>
            ))}
          </select>
          <Button variant="outline" onClick={doMerge} disabled={!mergeFrom || merge.isPending}>
            {t("orders.merge")}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">{t("orders.mergeHint")}</p>
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
  const { t } = useTranslation()
  const invoice = useOrderInvoice(order.id)
  const issue = useIssueInvoice(order.id)
  const [docType, setDocType] = useState<DocType>("CONSUMIDOR_FINAL")
  const [docNumber, setDocNumber] = useState("")

  const emitir = () => {
    const needsDoc = docType !== "CONSUMIDOR_FINAL"
    const number = needsDoc ? docNumber.trim() : "0"
    if (needsDoc && !/^\d{7,11}$/.test(number)) {
      toast.error(t("orders.toasts.invalidDoc"))
      return
    }
    issue.mutate(
      { doc_type: docType, doc_number: number },
      {
        onSuccess: (inv) => {
          if (inv.status === "AUTHORIZED")
            toast.success(t("orders.toasts.invoiceAuthorized", { cae: inv.cae }))
          else
            toast.error(
              inv.rejection
                ? t("orders.toasts.invoiceRejectedReason", { reason: inv.rejection })
                : t("orders.toasts.invoiceRejected")
            )
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("orders.errors.issueFailed"))),
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
            <span>{t("orders.invoicing")}</span>
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
            <span className="text-muted-foreground">{t("orders.cae")}</span>
            <span className="font-mono text-xs">{existing.cae}</span>
          </div>
          {existing.cae_expiration ? (
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t("orders.caeExpiration")}</span>
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
        <CardTitle>{t("orders.invoice")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {existing && existing.status === "REJECTED" ? (
          <p className="rounded-md border border-destructive/40 bg-destructive/5 p-2 text-xs text-destructive">
            {existing.rejection
              ? t("orders.invoiceLastRejectedReason", { reason: existing.rejection })
              : t("orders.invoiceLastRejected")}
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
          {issue.isPending ? t("orders.issuing") : t("orders.issueInvoice")}
        </Button>
        <p className="text-xs text-muted-foreground">{t("orders.invoiceHint")}</p>
      </CardContent>
    </Card>
  )
}

// El total del ticket: con desglose de impuesto cuando hay sales tax a sumar
// (US); si el impuesto es 0 (AR/IVA incluido) muestra sólo "Total" como siempre.
function OrderTotalBreakdown({
  orderId,
  subtotal,
  currency,
}: {
  orderId: string
  subtotal: number
  currency: string
}) {
  const { t } = useTranslation()
  const quote = useOrderTaxQuote(orderId, subtotal)
  const q = quote.data
  if (!q || q.tax_amount <= 0) {
    return (
      <div className="mt-3 flex items-center justify-between border-t pt-3 text-sm font-medium">
        <span>{t("orders.total")}</span>
        <span>{formatMoney(subtotal, currency)}</span>
      </div>
    )
  }
  return (
    <div className="mt-3 space-y-1 border-t pt-3 text-sm">
      <div className="flex items-center justify-between text-muted-foreground">
        <span>{t("orders.subtotal")}</span>
        <span>{formatMoney(q.subtotal_amount, currency)}</span>
      </div>
      <div className="flex items-center justify-between text-muted-foreground">
        <span>{t("orders.taxLine", { rate: (q.rate_bps / 100).toFixed(2) })}</span>
        <span>{formatMoney(q.tax_amount, currency)}</span>
      </div>
      <div className="flex items-center justify-between font-medium text-foreground">
        <span>{t("orders.total")}</span>
        <span>{formatMoney(q.total_amount, currency)}</span>
      </div>
    </div>
  )
}

function CobroSection({
  order,
  tableLabel,
  onPendingOnline,
}: {
  order: OrderDTO
  tableLabel: string
  onPendingOnline: () => void
}) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const payments = useOrderPayments(order.id)
  const registerPayment = useRegisterPayment(order.id)
  const refundPayment = useRefundPayment(order.id)
  const reopenOrder = useReopenOrder(order.id)
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [amount, setAmount] = useState("")
  const [tip, setTip] = useState("")
  const [splitMode, setSplitMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null)

  const taxQuote = useOrderTaxQuote(order.id, order.total_amount)
  // Lo que se cobra es el total CON impuesto (US); en AR el tax es 0 → total ==
  // subtotal, así que el restante queda idéntico a hoy (paridad).
  const chargeableTotal = taxQuote.data?.total_amount ?? order.total_amount
  const list = payments.data ?? []
  const confirmed = list
    .filter((p) => p.direction === "INFLOW" && p.status === "CONFIRMED")
    .reduce((sum, p) => sum + p.amount, 0)
  const remaining = Math.max(chargeableTotal - confirmed, 0)
  const isPaid = order.status === "PAID"
  const splitAmount = sumLineItems(order.items, selected)
  // Impuesto proporcional del split: la tasa efectiva de la orden aplicada al
  // subtotal seleccionado. 0 en AR (rate 0) → el split queda pre-tax como antes.
  const taxRateBps = taxQuote.data?.rate_bps ?? 0
  const splitTax = Math.round((splitAmount * taxRateBps) / 10000)

  // What the cashier types is in pesos; the API works in minor units. In split
  // mode the amount comes from the selected items instead.
  const computeCharge = (): number => {
    if (splitMode) return splitAmount + splitTax
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
      toast.error(t("orders.toasts.invalidAmount"))
      return
    }
    const tipMinor = tip.trim() ? Math.round(Number(tip) * 100) : 0
    if (!Number.isFinite(tipMinor) || tipMinor < 0) {
      toast.error(t("orders.toasts.invalidTip"))
      return
    }
    // El impuesto de ESTE cobro: sólo cuando se paga el total con impuesto de una
    // sola vez (no split, sin monto manual, sin cobros previos). Parcial/split → 0
    // (queda como follow-up; consistente con que el split hoy es pre-tax).
    const q = taxQuote.data
    const taxForCharge = splitMode
      ? splitTax
      : !amount.trim() && confirmed === 0 && q && q.tax_amount > 0
        ? q.tax_amount
        : 0
    setCheckoutUrl(null)
    registerPayment.mutate(
      { method, amount: minor, tip: tipMinor, tax: taxForCharge },
      {
        onSuccess: (payment) => {
          setAmount("")
          setTip("")
          setSelected(new Set())
          setSplitMode(false)
          if (payment.status === "PENDING" && payment.checkout_url) {
            setCheckoutUrl(payment.checkout_url)
            onPendingOnline()
            toast.info(t("orders.toasts.paymentLinkGenerated"))
          } else {
            toast.success(t("orders.toasts.chargeRegistered"))
          }
        },
        onError: (error) => {
          // Guarda B3: si el local exige caja abierta y no la hay, el back devuelve
          // 409 → ofrecemos abrir la caja en vez de solo mostrar el error.
          if (isApiError(error) && error.code === "no_open_cash_session") {
            toast.error(apiErrorText(error, t, error.message), {
              action: { label: t("orders.openCashRegister"), onClick: () => navigate("/app/caja") },
            })
            return
          }
          toast.error(apiErrorText(error, t, t("orders.errors.chargeFailed")))
        },
      }
    )
  }

  const doRefund = (paymentId: string) => {
    refundPayment.mutate(paymentId, {
      onSuccess: () => toast.success(t("orders.toasts.paymentRefunded")),
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.refundFailed"))),
    })
  }

  const doReopen = () => {
    if (!window.confirm(t("orders.toasts.reopenConfirm"))) {
      return
    }
    reopenOrder.mutate(undefined, {
      onSuccess: () => toast.success(t("orders.toasts.orderReopened")),
      onError: (error) =>
        toast.error(apiErrorText(error, t, t("orders.errors.reopenFailed"))),
    })
  }

  const printReceipt = () => {
    const printedAt = new Date().toLocaleString(dateLocale(), {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
    const confirmedInflows = list.filter(
      (p) => p.direction === "INFLOW" && p.status === "CONFIRMED"
    )
    const paid = confirmedInflows.map((p) => ({
      label: t(`orders.paymentMethods.${p.method}`),
      amount: p.amount,
    }))
    const tipTotal = confirmedInflows.reduce((sum, p) => sum + p.tip_amount, 0)
    const q = taxQuote.data
    const tax =
      q && q.tax_amount > 0
        ? {
            subtotal: q.subtotal_amount,
            amount: q.tax_amount,
            total: q.total_amount,
            rateBps: q.rate_bps,
          }
        : null
    printTicket(
      receiptHtml(order, tableLabel, printedAt, paid, tipTotal, tax, {
        nonFiscal: t("orders.ticket.nonFiscal"),
        subtotal: t("orders.ticket.subtotal"),
        tax: (rate) => t("orders.ticket.taxRate", { rate }),
        total: t("orders.ticket.total"),
        tip: t("orders.ticket.tip"),
      }),
      t("orders.ticket.windowTitle")
    )
  }

  const hasConfirmed = list.some(
    (p) => p.direction === "INFLOW" && p.status === "CONFIRMED"
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{t("orders.charge")}</span>
          <span className="flex items-center gap-2">
            {hasConfirmed ? (
              <Button variant="outline" size="sm" onClick={printReceipt}>
                {t("orders.receipt")}
              </Button>
            ) : null}
            {isPaid ? (
              <Button
                variant="outline"
                size="sm"
                onClick={doReopen}
                disabled={reopenOrder.isPending}
              >
                {t("orders.reopen")}
              </Button>
            ) : null}
            {isPaid ? (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                {t("orders.paid")}
              </span>
            ) : null}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {list.length > 0 ? (
          <ul className="flex flex-col divide-y divide-border text-sm">
            {list.map((p) => (
              <li key={p.id} className="flex items-center justify-between py-1.5">
                <span className="text-muted-foreground">
                  {t(`orders.paymentMethods.${p.method}`)}
                </span>
                <span className="flex items-center gap-2">
                  {formatMoney(p.amount, p.currency)}
                  <span
                    className={
                      p.status === "CONFIRMED"
                        ? "text-xs text-emerald-600"
                        : p.status === "REFUNDED"
                          ? "text-xs text-muted-foreground line-through"
                          : "text-xs text-amber-600"
                    }
                  >
                    {p.status === "CONFIRMED"
                      ? t("orders.paymentStatus.confirmed")
                      : p.status === "REFUNDED"
                        ? t("orders.paymentStatus.refunded")
                        : t("orders.paymentStatus.pending")}
                  </span>
                  {p.direction === "INFLOW" && p.status === "CONFIRMED" ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs text-destructive"
                      disabled={refundPayment.isPending}
                      onClick={() => doRefund(p.id)}
                    >
                      {t("orders.cancelPayment")}
                    </Button>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        ) : null}

        {!isPaid ? (
          <div className="flex items-center justify-between text-sm font-medium">
            <span>{t("orders.remaining")}</span>
            <span>{formatMoney(remaining, order.currency)}</span>
          </div>
        ) : null}

        {!isPaid ? (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              {PAYMENT_METHODS.map((m) => (
                <Button
                  key={m}
                  type="button"
                  size="sm"
                  variant={method === m ? "default" : "outline"}
                  onClick={() => setMethod(m)}
                >
                  {t(`orders.paymentMethods.${m}`)}
                </Button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setSplitMode((s) => !s)}
              className="self-start text-xs text-muted-foreground underline underline-offset-4"
            >
              {splitMode ? t("orders.chargeAnAmount") : t("orders.splitByItem")}
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
                {splitTax > 0 ? (
                  <>
                    <div className="mt-1 flex justify-between border-t pt-1 text-muted-foreground">
                      <span>{t("orders.selected")}</span>
                      <span>{formatMoney(splitAmount, order.currency)}</span>
                    </div>
                    <div className="flex justify-between text-muted-foreground">
                      <span>{t("orders.taxLine", { rate: (taxRateBps / 100).toFixed(2) })}</span>
                      <span>{formatMoney(splitTax, order.currency)}</span>
                    </div>
                    <div className="flex justify-between font-medium">
                      <span>{t("orders.total")}</span>
                      <span>{formatMoney(splitAmount + splitTax, order.currency)}</span>
                    </div>
                  </>
                ) : (
                  <div className="mt-1 flex justify-between border-t pt-1 font-medium">
                    <span>{t("orders.selected")}</span>
                    <span>{formatMoney(splitAmount, order.currency)}</span>
                  </div>
                )}
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

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{t("orders.tip")}</span>
              <Input
                type="number"
                min={0}
                step="0.01"
                placeholder="0.00"
                value={tip}
                onChange={(e) => setTip(e.target.value)}
                className="max-w-[8rem]"
              />
            </div>

            <Button
              onClick={cobrar}
              disabled={registerPayment.isPending || (splitMode && splitAmount < 1)}
            >
              {registerPayment.isPending
                ? "…"
                : t("orders.chargeAmount", { amount: formatMoney(computeCharge(), order.currency) })}
            </Button>
          </div>
        ) : null}

        {checkoutUrl && !isPaid ? (
          <div className="flex flex-col gap-2 rounded-md border border-dashed p-3 text-sm">
            <p className="text-muted-foreground">
              {t("orders.onlinePaymentWaiting")}
            </p>
            <Button asChild variant="outline">
              <a href={checkoutUrl} target="_blank" rel="noreferrer">
                {t("orders.openCheckout")}
              </a>
            </Button>
            <Spinner className="size-4 self-center text-muted-foreground" />
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
