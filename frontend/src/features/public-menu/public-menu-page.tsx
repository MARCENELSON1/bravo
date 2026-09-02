import { Minus, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { useParams, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type {
  PublicMenuCategoryDTO,
  PublicMenuItemDTO,
  PublicMenuModifierGroupDTO,
  TableBillDTO,
} from "@/api/public-menu-api"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  buildLine,
  cartCount,
  cartTotal,
  isSelectionValid,
  lineKey,
  toOrderLines,
  type CartLine,
} from "@/features/public-menu/public-menu-cart"
import {
  useCallWaiter,
  usePaymentReceipt,
  usePayTableBill,
  usePaymentStatus,
  usePublicMenu,
  useRequestBill,
  useSubmitCustomerOrder,
  useTableBill,
} from "@/hooks/use-public-menu"
import { formatMoney } from "@/lib/money"
import { cn } from "@/lib/utils"

// El pago iniciado se recuerda por mesa (sessionStorage): si el comensal va a
// MercadoPago y vuelve, retomamos el poll del estado y le mostramos "pagado".
const payKey = (token: string) => `wellnod_pay_${token}`
function readStoredPayment(token: string | undefined): string | null {
  if (!token) return null
  try {
    return sessionStorage.getItem(payKey(token))
  } catch {
    return null
  }
}

// Al volver de MercadoPago retomamos el pago: primero por nuestro marcador
// (sessionStorage, misma sesión); si se perdió, por el `external_reference` que MP
// agrega a la URL (`<tenant>:<payment_id>`) → así el "¡Pagado!" aparece igual.
function resumePaymentId(token: string | undefined, params: URLSearchParams): string | null {
  const stored = readStoredPayment(token)
  if (stored) return stored
  const ref = params.get("external_reference")
  if (ref && ref.includes(":")) return ref.split(":")[1] || null
  return null
}

// Carta pública de cara al comensal (ruta /carta/:token, SIN auth). Mobile-first,
// theme-aware. Con autopedido prendido (F2): carrito line-based (un ítem puede
// entrar con distintos modificadores) + picker de opciones + envío.
export function PublicMenuPage() {
  const { t } = useTranslation()
  const { token } = useParams<{ token: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data, isLoading, isError, error } = usePublicMenu(token)
  const callWaiter = useCallWaiter(token)
  const requestBill = useRequestBill(token)
  const submitOrder = useSubmitCustomerOrder(token)
  const bill = useTableBill(token)
  const payBill = usePayTableBill(token)
  const [cart, setCart] = useState<CartLine[]>([])
  const [picker, setPicker] = useState<PublicMenuItemDTO | null>(null)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  const [idemKey, setIdemKey] = useState(() => crypto.randomUUID())
  const [paymentId, setPaymentId] = useState<string | null>(() =>
    resumePaymentId(token, searchParams)
  )
  const paymentStatus = usePaymentStatus(token, paymentId)

  const clearPayment = () => {
    if (token) {
      try {
        sessionStorage.removeItem(payKey(token))
      } catch {
        /* private mode / storage blocked → nothing to clear */
      }
    }
    // Sacamos los params que agregó MercadoPago para que un refresh no vuelva a
    // retomar el pago ya cerrado.
    if (searchParams.has("external_reference")) {
      setSearchParams({}, { replace: true })
    }
    setPaymentId(null)
    void bill.refetch()
  }
  const payStatus = paymentStatus.data?.status

  if (isLoading) {
    return <StateScreen>{t("publicMenu.loading")}</StateScreen>
  }

  if (isError || !data) {
    const invalid = isApiError(error) && error.code === "invalid_table_qr_token"
    return (
      <StateScreen title={t(invalid ? "publicMenu.invalid.title" : "publicMenu.error.title")}>
        {t(invalid ? "publicMenu.invalid.body" : "publicMenu.error.body")}
      </StateScreen>
    )
  }

  if (submitOrder.isSuccess && submitOrder.data) {
    const gated = submitOrder.data.requires_confirmation
    return (
      <StateScreen
        title={t("publicMenu.sent.title")}
        action={
          <Button
            onClick={() => {
              submitOrder.reset()
              setCart([])
            }}
          >
            {t("publicMenu.sent.again")}
          </Button>
        }
      >
        {t(gated ? "publicMenu.sent.gated" : "publicMenu.sent.kitchen")}
      </StateScreen>
    )
  }

  // Pago en curso (recién iniciado o retomado al volver de MercadoPago): la
  // pantalla de estado toma toda la vista hasta confirmar o volver a la carta.
  if (paymentId) {
    if (payStatus === "CONFIRMED") {
      return <PaidScreen token={token} paymentId={paymentId} onDone={clearPayment} />
    }
    if (payStatus === "FAILED" || paymentStatus.isError) {
      return (
        <StateScreen
          title={t("publicMenu.pay.failed.title")}
          action={<Button onClick={clearPayment}>{t("publicMenu.pay.failed.retry")}</Button>}
        >
          {t("publicMenu.pay.failed.body")}
        </StateScreen>
      )
    }
    return (
      <StateScreen title={t("publicMenu.pay.confirming.title")}>
        {t("publicMenu.pay.confirming.body")}
      </StateScreen>
    )
  }

  const selfOrderEnabled = data.self_order_enabled === true
  const categories = data.categories.filter((c) => c.items.length > 0)
  const count = cartCount(cart)
  const total = cartTotal(cart)
  const currency = data.currency
  const showCartBar = selfOrderEnabled && count > 0

  const addLine = (item: PublicMenuItemDTO, optionIds: string[]) =>
    setCart((prev) => {
      const key = lineKey(item.id, optionIds)
      if (prev.some((l) => l.key === key)) {
        return prev.map((l) => (l.key === key ? { ...l, quantity: l.quantity + 1 } : l))
      }
      return [...prev, buildLine(item, optionIds)]
    })

  const setQty = (key: string, qty: number) =>
    setCart((prev) =>
      qty <= 0
        ? prev.filter((l) => l.key !== key)
        : prev.map((l) => (l.key === key ? { ...l, quantity: qty } : l))
    )

  const onCallWaiter = () =>
    callWaiter.mutate(undefined, {
      onSuccess: () => toast.success(t("publicMenu.toast.waiterOnTheWay")),
      onError: () => toast.error(t("publicMenu.toast.failed")),
    })
  const onRequestBill = () =>
    requestBill.mutate(undefined, {
      onSuccess: () => toast.success(t("publicMenu.toast.billOnTheWay")),
      onError: () => toast.error(t("publicMenu.toast.failed")),
    })
  const onSubmitOrder = () =>
    submitOrder.mutate(toOrderLines(cart), {
      onError: (e) => {
        const unavailable = isApiError(e) && e.code === "product_unavailable"
        toast.error(
          t(unavailable ? "publicMenu.toast.orderUnavailable" : "publicMenu.toast.orderFailed")
        )
      },
    })

  // El local ofrece pago online (cobro prendido + MercadoPago conectado) y hay
  // saldo → mostramos "Pagar" en vez de "Pedir la cuenta" (F1 queda de fallback).
  const billData = bill.data
  const canPay = billData?.online_pay_available === true && billData.balance > 0
  const openPay = () => {
    setIdemKey(crypto.randomUUID()) // una clave nueva por intento (retries la reusan)
    setPayOpen(true)
  }
  const onPay = (tip: number, amount: number | null) =>
    payBill.mutate(
      { tip, amount, idempotencyKey: idemKey },
      {
        onSuccess: (result) => {
          try {
            if (token) sessionStorage.setItem(payKey(token), result.payment_id)
          } catch {
            /* private mode → sin persistencia; el flujo sigue en memoria */
          }
          setPayOpen(false)
          if (result.checkout_url) {
            // Redirigimos a MercadoPago. OJO: NO seteamos paymentId acá — si lo
            // hiciéramos, arrancaría el poll de estado y la navegación saliente lo
            // abortaría, lo que React Query marca como error y hace parpadear la
            // pantalla de "pago fallido". Al volver de MP el pago se retoma solo
            // (sessionStorage / external_reference).
            window.location.href = result.checkout_url
          } else {
            // Sin checkout_url (el gateway ya confirmó, ej. manual): mostramos el
            // estado ahora, sin redirect.
            setPaymentId(result.payment_id)
          }
        },
        onError: () => toast.error(t("publicMenu.toast.payFailed")),
      }
    )

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border/60 bg-background/80 px-5 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-xl items-center gap-3">
          <WellnodMark className="h-7 w-auto shrink-0 text-foreground" />
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold leading-tight">{data.tenant_name}</h1>
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              {t("publicMenu.menu")}
            </p>
          </div>
        </div>
      </header>

      <main className={cn("mx-auto max-w-xl px-5 pt-6", showCartBar ? "pb-40" : "pb-28")}>
        {categories.length === 0 ? (
          <StateScreen title={t("publicMenu.empty.title")} bare>
            {t("publicMenu.empty.body")}
          </StateScreen>
        ) : (
          <div className="flex flex-col gap-8">
            {categories.map((category) => (
              <MenuSection
                key={category.name ?? "__uncategorized__"}
                category={category}
                currency={currency}
                fallbackLabel={t("publicMenu.uncategorized")}
                selfOrderEnabled={selfOrderEnabled}
                cart={cart}
                onAddPlain={(item) => addLine(item, [])}
                onChangeQty={setQty}
                onOpenPicker={setPicker}
              />
            ))}
          </div>
        )}
        <p className="mt-10 text-center text-xs text-muted-foreground">
          {t("publicMenu.poweredBy")}
        </p>
      </main>

      {/* Barra fija: ver/enviar el pedido + avisar al salón. */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-border/60 bg-background/90 px-5 py-3 backdrop-blur-xl">
        <div className="mx-auto flex max-w-xl flex-col gap-3">
          {showCartBar ? (
            <Button
              className="w-full justify-between"
              onClick={() => setReviewOpen(true)}
            >
              <span>{`${t("publicMenu.cart.review")} · ${count}`}</span>
              <span className="tabular-nums">{formatMoney(total, currency)}</span>
            </Button>
          ) : null}
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={onCallWaiter}
              disabled={callWaiter.isPending}
            >
              {t("publicMenu.actions.callWaiter")}
            </Button>
            {canPay ? (
              <Button
                variant={showCartBar ? "outline" : "default"}
                className="flex-1"
                onClick={openPay}
                disabled={payBill.isPending}
              >
                {t("publicMenu.pay.action")}
              </Button>
            ) : (
              <Button
                variant={showCartBar ? "outline" : "default"}
                className="flex-1"
                onClick={onRequestBill}
                disabled={requestBill.isPending}
              >
                {t("publicMenu.actions.requestBill")}
              </Button>
            )}
          </div>
        </div>
      </div>

      <ModifierPicker
        item={picker}
        currency={currency}
        onClose={() => setPicker(null)}
        onAdd={(item, optionIds) => {
          addLine(item, optionIds)
          setPicker(null)
        }}
      />

      <CartReviewSheet
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        cart={cart}
        currency={currency}
        onChangeQty={setQty}
        onSubmit={onSubmitOrder}
        submitting={submitOrder.isPending}
      />

      {billData ? (
        <PaySheet
          open={payOpen}
          onOpenChange={setPayOpen}
          bill={billData}
          onPay={onPay}
          paying={payBill.isPending}
        />
      ) : null}
    </div>
  )
}

// Presets de propina (%) sobre lo que este comensal paga. 0 = sin propina; "custom"
// abre un monto a mano. Si el dueño la desactivó, el selector no se muestra.
const TIP_PRESETS = [0, 10, 15, 20] as const
const MIN_SPLIT = 2
const MAX_SPLIT = 12

// Cómo divide el comensal: todo el saldo, su parte (÷ N), o un monto a mano.
type PayMode = "all" | "split" | "custom"

// Pantalla de pago (Sheet inferior): la cuenta + dividir la cuenta + propina +
// "Pagar $X". El saldo lo acota el server; el comensal elige cuánto y la propina.
function PaySheet({
  open,
  onOpenChange,
  bill,
  onPay,
  paying,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  bill: TableBillDTO
  onPay: (tip: number, amount: number | null) => void
  paying: boolean
}) {
  const { t } = useTranslation()
  const [mode, setMode] = useState<PayMode>("all")
  const [splitN, setSplitN] = useState(MIN_SPLIT)
  const [customAmount, setCustomAmount] = useState<string>("")
  const [tipPct, setTipPct] = useState<number>(0)
  const [customTip, setCustomTip] = useState<string>("")
  const [tipCustomOpen, setTipCustomOpen] = useState(false)

  const balance = bill.balance
  const currency = bill.currency
  const toMinor = (s: string) => Math.max(0, Math.round(Number(s.replace(",", ".")) * 100) || 0)

  // Cuánto paga este comensal (acotado al saldo). `all` manda null → el server
  // cobra todo el saldo vigente (a prueba de carreras).
  const share =
    mode === "split"
      ? Math.min(Math.round(balance / splitN), balance)
      : mode === "custom"
        ? Math.min(toMinor(customAmount), balance)
        : balance
  const payAmount: number | null = mode === "all" ? null : share

  const tip = bill.tips_enabled
    ? tipCustomOpen
      ? toMinor(customTip)
      : Math.round((share * tipPct) / 100)
    : 0
  const total = share + tip

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="mx-auto max-w-xl gap-0 rounded-t-2xl px-5 pb-5">
        <SheetHeader className="px-0">
          <SheetTitle>{t("publicMenu.pay.title")}</SheetTitle>
        </SheetHeader>

        <div className="max-h-[32svh] divide-y divide-border/50 overflow-y-auto py-1">
          {bill.items.map((item, i) => (
            <div key={i} className="flex items-start justify-between gap-3 py-2 text-sm">
              <span className="min-w-0">
                <span className="tabular-nums text-muted-foreground">{item.quantity}× </span>
                {item.name}
                {item.selected_options && item.selected_options.length > 0 ? (
                  <span className="block text-xs text-muted-foreground">
                    {item.selected_options.map((o) => o.name).join(", ")}
                  </span>
                ) : null}
              </span>
              <span className="shrink-0 tabular-nums">
                {formatMoney(item.unit_price * item.quantity, currency)}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-2 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{t("publicMenu.pay.balance")}</span>
          <span className="tabular-nums font-medium">{formatMoney(balance, currency)}</span>
        </div>

        {/* Dividir la cuenta: todo / mi parte (÷ N) / otro monto. Parciales acumulan. */}
        <div className="mt-4">
          <p className="mb-2 text-sm font-medium">{t("publicMenu.pay.split.title")}</p>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant={mode === "all" ? "default" : "outline"}
              onClick={() => setMode("all")}
            >
              {t("publicMenu.pay.split.all")}
            </Button>
            <Button
              size="sm"
              variant={mode === "split" ? "default" : "outline"}
              onClick={() => setMode("split")}
            >
              {t("publicMenu.pay.split.mine")}
            </Button>
            <Button
              size="sm"
              variant={mode === "custom" ? "default" : "outline"}
              onClick={() => setMode("custom")}
            >
              {t("publicMenu.pay.split.other")}
            </Button>
          </div>
          {mode === "split" ? (
            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {t("publicMenu.pay.split.between")}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  size="icon"
                  variant="outline"
                  className="h-8 w-8"
                  disabled={splitN <= MIN_SPLIT}
                  onClick={() => setSplitN((n) => Math.max(MIN_SPLIT, n - 1))}
                  aria-label={t("publicMenu.pay.split.fewer")}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-6 text-center tabular-nums text-sm font-semibold">{splitN}</span>
                <Button
                  size="icon"
                  variant="outline"
                  className="h-8 w-8"
                  disabled={splitN >= MAX_SPLIT}
                  onClick={() => setSplitN((n) => Math.min(MAX_SPLIT, n + 1))}
                  aria-label={t("publicMenu.pay.split.more")}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ) : null}
          {mode === "custom" ? (
            <input
              type="number"
              inputMode="decimal"
              min={0}
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              aria-label={t("publicMenu.pay.split.amountLabel")}
              className="mt-3 w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm tabular-nums outline-none focus:border-primary"
              placeholder="0"
            />
          ) : null}
        </div>

        {bill.tips_enabled ? (
          <div className="mt-4">
            <p className="mb-2 text-sm font-medium">{t("publicMenu.pay.tip")}</p>
            <div className="flex flex-wrap gap-2">
              {TIP_PRESETS.map((pct) => (
                <Button
                  key={pct}
                  size="sm"
                  variant={!tipCustomOpen && tipPct === pct ? "default" : "outline"}
                  onClick={() => {
                    setTipCustomOpen(false)
                    setTipPct(pct)
                  }}
                >
                  {pct === 0 ? t("publicMenu.pay.noTip") : `${pct}%`}
                </Button>
              ))}
              <Button
                size="sm"
                variant={tipCustomOpen ? "default" : "outline"}
                onClick={() => setTipCustomOpen(true)}
              >
                {t("publicMenu.pay.tipCustom")}
              </Button>
            </div>
            {tipCustomOpen ? (
              <input
                type="number"
                inputMode="decimal"
                min={0}
                value={customTip}
                onChange={(e) => setCustomTip(e.target.value)}
                aria-label={t("publicMenu.pay.tipCustomLabel")}
                className="mt-3 w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm tabular-nums outline-none focus:border-primary"
                placeholder="0"
              />
            ) : null}
          </div>
        ) : null}

        <Button
          className="mt-5 w-full justify-between"
          disabled={paying || share <= 0}
          onClick={() => onPay(tip, payAmount)}
        >
          <span>{paying ? t("publicMenu.pay.paying") : t("publicMenu.pay.action")}</span>
          <span className="tabular-nums">{formatMoney(total, currency)}</span>
        </Button>
      </SheetContent>
    </Sheet>
  )
}

function MenuSection({
  category,
  currency,
  fallbackLabel,
  selfOrderEnabled,
  cart,
  onAddPlain,
  onChangeQty,
  onOpenPicker,
}: {
  category: PublicMenuCategoryDTO
  currency: string
  fallbackLabel: string
  selfOrderEnabled: boolean
  cart: CartLine[]
  onAddPlain: (item: PublicMenuItemDTO) => void
  onChangeQty: (key: string, qty: number) => void
  onOpenPicker: (item: PublicMenuItemDTO) => void
}) {
  const { t } = useTranslation()
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {category.name ?? fallbackLabel}
      </h2>
      <ul className="flex flex-col divide-y divide-border/50">
        {category.items.map((item) => {
          const soldOut = item.available_today === false
          const hasModifiers = (item.modifier_groups?.length ?? 0) > 0
          const plainKey = lineKey(item.id, [])
          const plainQty = cart.find((l) => l.key === plainKey)?.quantity ?? 0
          const inCart = cart
            .filter((l) => l.productId === item.id)
            .reduce((n, l) => n + l.quantity, 0)
          return (
            <li
              key={item.id}
              className={cn("flex items-start gap-3 py-3", soldOut && "opacity-50")}
            >
              {item.image_url ? (
                <img
                  src={item.image_url}
                  alt=""
                  loading="lazy"
                  className="h-14 w-14 shrink-0 rounded-lg object-cover"
                />
              ) : null}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[15px] leading-snug">{item.name}</span>
                  {soldOut ? (
                    <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      {t("publicMenu.soldOut")}
                    </span>
                  ) : null}
                </div>
                {item.description ? (
                  <p className="mt-0.5 text-xs leading-snug text-muted-foreground">
                    {item.description}
                  </p>
                ) : null}
              </div>
              <div className="flex shrink-0 flex-col items-end gap-2">
                <span className="tabular-nums font-medium">
                  {formatMoney(item.price_amount, currency)}
                </span>
                {selfOrderEnabled && !soldOut ? (
                  hasModifiers ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8"
                      onClick={() => onOpenPicker(item)}
                    >
                      {t("publicMenu.cart.add")}
                      {inCart > 0 ? <span className="ml-1 tabular-nums">· {inCart}</span> : null}
                    </Button>
                  ) : (
                    <QtyStepper
                      qty={plainQty}
                      onDecrease={() => onChangeQty(plainKey, plainQty - 1)}
                      onIncrease={() => onAddPlain(item)}
                    />
                  )
                ) : null}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

// Selector de cantidad por ítem: "+" hasta que hay ≥1, ahí aparece [− n +].
function QtyStepper({
  qty,
  onDecrease,
  onIncrease,
}: {
  qty: number
  onDecrease: () => void
  onIncrease: () => void
}) {
  const { t } = useTranslation()
  if (qty <= 0) {
    return (
      <Button
        size="icon"
        variant="outline"
        className="h-8 w-8"
        onClick={onIncrease}
        aria-label={t("publicMenu.cart.increase")}
      >
        <Plus className="h-4 w-4" />
      </Button>
    )
  }
  return (
    <div className="flex items-center gap-2">
      <Button
        size="icon"
        variant="outline"
        className="h-8 w-8"
        onClick={onDecrease}
        aria-label={t("publicMenu.cart.decrease")}
      >
        <Minus className="h-4 w-4" />
      </Button>
      <span className="w-5 text-center tabular-nums text-sm font-semibold">{qty}</span>
      <Button
        size="icon"
        variant="outline"
        className="h-8 w-8"
        onClick={onIncrease}
        aria-label={t("publicMenu.cart.increase")}
      >
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  )
}

// Picker de modificadores (Sheet inferior). Respeta min/max por grupo; el botón
// "Agregar" se habilita solo cuando la selección es válida.
function ModifierPicker({
  item,
  currency,
  onClose,
  onAdd,
}: {
  item: PublicMenuItemDTO | null
  currency: string
  onClose: () => void
  onAdd: (item: PublicMenuItemDTO, optionIds: string[]) => void
}) {
  const { t } = useTranslation()
  const [selected, setSelected] = useState<Record<string, string[]>>({})

  // Reinicia la selección cada vez que se abre un ítem distinto.
  const [openedFor, setOpenedFor] = useState<string | null>(null)
  if (item && openedFor !== item.id) {
    setOpenedFor(item.id)
    setSelected({})
  }

  const groups = item?.modifier_groups ?? []
  const selectedIds = Object.values(selected).flat()
  const valid = item ? isSelectionValid(groups, selectedIds) : false

  const toggle = (group: PublicMenuModifierGroupDTO, optionId: string) =>
    setSelected((prev) => {
      const cur = prev[group.id] ?? []
      const has = cur.includes(optionId)
      let next: string[]
      if (group.max_select === 1) {
        next = [optionId] // radio: reemplaza
      } else if (has) {
        next = cur.filter((x) => x !== optionId)
      } else if (cur.length >= group.max_select) {
        return prev // llegó al máximo
      } else {
        next = [...cur, optionId]
      }
      return { ...prev, [group.id]: next }
    })

  return (
    <Sheet open={item != null} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom" className="mx-auto max-w-xl gap-0 rounded-t-2xl px-5 pb-5">
        {item ? (
          <>
            <SheetHeader className="px-0">
              <SheetTitle>{item.name}</SheetTitle>
            </SheetHeader>
            <div className="max-h-[55svh] overflow-y-auto py-2">
              {groups.map((group) => (
                <div key={group.id} className="mb-4">
                  <div className="mb-2 flex items-center gap-2">
                    <h3 className="text-sm font-semibold">{group.name}</h3>
                    <span className="text-xs text-muted-foreground">
                      {group.required
                        ? t("publicMenu.picker.required")
                        : group.max_select > 1
                          ? t("publicMenu.picker.upTo", { max: group.max_select })
                          : t("publicMenu.picker.pickOne")}
                    </span>
                  </div>
                  <ul className="flex flex-col divide-y divide-border/50">
                    {group.options.map((option) => {
                      const checked = (selected[group.id] ?? []).includes(option.id)
                      return (
                        <li key={option.id}>
                          <label className="flex cursor-pointer items-center gap-3 py-2.5">
                            <input
                              type={group.max_select === 1 ? "radio" : "checkbox"}
                              name={group.id}
                              className="size-4 accent-primary"
                              checked={checked}
                              onChange={() => toggle(group, option.id)}
                            />
                            <span className="flex-1 text-sm">{option.name}</span>
                            {option.price_delta > 0 ? (
                              <span className="tabular-nums text-sm text-muted-foreground">
                                +{formatMoney(option.price_delta, currency)}
                              </span>
                            ) : null}
                          </label>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ))}
            </div>
            <Button
              className="w-full"
              disabled={!valid}
              onClick={() => onAdd(item, selectedIds)}
            >
              {t("publicMenu.picker.add")}
            </Button>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

// Revisión del pedido (Sheet inferior): líneas con cantidad + quitar, total, enviar.
function CartReviewSheet({
  open,
  onOpenChange,
  cart,
  currency,
  onChangeQty,
  onSubmit,
  submitting,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  cart: CartLine[]
  currency: string
  onChangeQty: (key: string, qty: number) => void
  onSubmit: () => void
  submitting: boolean
}) {
  const { t } = useTranslation()
  const total = cartTotal(cart)
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="mx-auto max-w-xl gap-0 rounded-t-2xl px-5 pb-5">
        <SheetHeader className="px-0">
          <SheetTitle>{t("publicMenu.cart.title")}</SheetTitle>
        </SheetHeader>
        {cart.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {t("publicMenu.cart.empty")}
          </p>
        ) : (
          <>
            <ul className="max-h-[50svh] divide-y divide-border/50 overflow-y-auto py-1">
              {cart.map((line) => (
                <li key={line.key} className="flex items-start gap-3 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{line.name}</p>
                    {line.optionsLabel ? (
                      <p className="text-xs text-muted-foreground">{line.optionsLabel}</p>
                    ) : null}
                    <p className="mt-0.5 tabular-nums text-xs text-muted-foreground">
                      {formatMoney(line.unitPrice * line.quantity, currency)}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Button
                      size="icon"
                      variant="outline"
                      className="h-8 w-8"
                      onClick={() => onChangeQty(line.key, line.quantity - 1)}
                      aria-label={
                        line.quantity <= 1
                          ? t("publicMenu.cart.remove")
                          : t("publicMenu.cart.decrease")
                      }
                    >
                      {line.quantity <= 1 ? (
                        <Trash2 className="h-4 w-4" />
                      ) : (
                        <Minus className="h-4 w-4" />
                      )}
                    </Button>
                    <span className="w-5 text-center tabular-nums text-sm font-semibold">
                      {line.quantity}
                    </span>
                    <Button
                      size="icon"
                      variant="outline"
                      className="h-8 w-8"
                      onClick={() => onChangeQty(line.key, line.quantity + 1)}
                      aria-label={t("publicMenu.cart.increase")}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
            <div className="mb-3 mt-1 flex items-center justify-between text-sm font-semibold">
              <span>{t("publicMenu.cart.total")}</span>
              <span className="tabular-nums">{formatMoney(total, currency)}</span>
            </div>
            <Button className="w-full" onClick={onSubmit} disabled={submitting}>
              {submitting ? t("publicMenu.cart.sending") : t("publicMenu.cart.send")}
            </Button>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}

// Pantalla de "¡Pagado!" con el recibo (no fiscal): local + ítems + monto pagado
// + propina + fecha. El recibo se pide una vez, con el pago ya confirmado; si aún
// no llegó, se muestra igual el "¡Pagado!" (el recibo es aditivo).
function PaidScreen({
  token,
  paymentId,
  onDone,
}: {
  token: string | undefined
  paymentId: string
  onDone: () => void
}) {
  const { t } = useTranslation()
  const receipt = usePaymentReceipt(token, paymentId, true)
  const r = receipt.data

  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-background px-6 py-10 text-foreground">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 text-center">
          <WellnodMark className="mb-2 h-9 w-auto text-foreground/80" />
          <h1 className="text-lg font-semibold">{t("publicMenu.pay.paid.title")}</h1>
          <p className="max-w-xs text-sm text-muted-foreground">{t("publicMenu.pay.paid.body")}</p>
        </div>

        {r ? (
          <div className="mt-6 rounded-2xl border border-border/60 bg-card p-5">
            <p className="text-center text-sm font-semibold">{r.venue_name}</p>
            {r.paid_at ? (
              <p className="mt-0.5 text-center text-xs text-muted-foreground">
                {formatDateTime(r.paid_at, r.currency)}
              </p>
            ) : null}
            {r.items.length > 0 ? (
              <ul className="mt-4 divide-y divide-border/50">
                {r.items.map((item, i) => (
                  <li key={i} className="flex items-start justify-between gap-3 py-1.5 text-sm">
                    <span className="min-w-0">
                      <span className="tabular-nums text-muted-foreground">{item.quantity}× </span>
                      {item.name}
                    </span>
                    <span className="shrink-0 tabular-nums">
                      {formatMoney(item.unit_price * item.quantity, r.currency)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
            <div className="mt-3 border-t border-border/60 pt-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t("publicMenu.pay.receipt.paid")}</span>
                <span className="tabular-nums font-medium">{formatMoney(r.amount, r.currency)}</span>
              </div>
              {r.tip > 0 ? (
                <div className="mt-1 flex justify-between">
                  <span className="text-muted-foreground">{t("publicMenu.pay.tip")}</span>
                  <span className="tabular-nums">{formatMoney(r.tip, r.currency)}</span>
                </div>
              ) : null}
            </div>
            <p className="mt-3 text-center text-[11px] text-muted-foreground">
              {t("publicMenu.pay.receipt.nonFiscal")}
            </p>
          </div>
        ) : null}

        <Button className="mt-6 w-full" onClick={onDone}>
          {t("publicMenu.menu")}
        </Button>
      </div>
    </div>
  )
}

function formatDateTime(iso: string, currency: string): string {
  const locale = currency?.toUpperCase() === "USD" ? "en-US" : "es-AR"
  try {
    return new Date(iso).toLocaleString(locale, { dateStyle: "short", timeStyle: "short" })
  } catch {
    return ""
  }
}

// Pantalla centrada para los estados (cargando / carta vacía / token inválido /
// pedido enviado). `action` opcional debajo del texto (ej. "Pedir algo más").
function StateScreen({
  title,
  children,
  action,
  bare = false,
}: {
  title?: string
  children?: ReactNode
  action?: ReactNode
  bare?: boolean
}) {
  const body = (
    <div className="flex flex-col items-center gap-2 text-center">
      <WellnodMark className="mb-2 h-9 w-auto text-foreground/80" />
      {title ? <h1 className="text-lg font-semibold">{title}</h1> : null}
      {children ? <p className="max-w-xs text-sm text-muted-foreground">{children}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
  if (bare) return <div className="py-16">{body}</div>
  return (
    <div className="flex min-h-svh items-center justify-center bg-background px-6 text-foreground">
      {body}
    </div>
  )
}
