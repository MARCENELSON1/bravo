import { Minus, Plus } from "lucide-react"
import { useState } from "react"
import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { PublicMenuCategoryDTO, PublicMenuItemDTO } from "@/api/public-menu-api"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { Button } from "@/components/ui/button"
import {
  useCallWaiter,
  usePublicMenu,
  useRequestBill,
  useSubmitCustomerOrder,
} from "@/hooks/use-public-menu"
import { formatMoney } from "@/lib/money"
import { cn } from "@/lib/utils"

// Carta pública de cara al comensal (ruta /carta/:token, SIN auth). Mobile-first,
// theme-aware (sigue el tema del navegador). El token porta el tenant → sin login.
// Con autopedido prendido (F2), suma carrito + envío; si no, se comporta como F1.
export function PublicMenuPage() {
  const { t } = useTranslation()
  const { token } = useParams<{ token: string }>()
  const { data, isLoading, isError, error } = usePublicMenu(token)
  const callWaiter = useCallWaiter(token)
  const requestBill = useRequestBill(token)
  const submitOrder = useSubmitCustomerOrder(token)
  // Carrito local: id de producto → cantidad. No se persiste (una sola visita).
  const [cart, setCart] = useState<Record<string, number>>({})

  if (isLoading) {
    return <StateScreen>{t("publicMenu.loading")}</StateScreen>
  }

  if (isError || !data) {
    // Token malformado/de otro tenant/expirado → pantalla amable "pedí el QR".
    const invalid = isApiError(error) && error.code === "invalid_table_qr_token"
    return (
      <StateScreen title={t(invalid ? "publicMenu.invalid.title" : "publicMenu.error.title")}>
        {t(invalid ? "publicMenu.invalid.body" : "publicMenu.error.body")}
      </StateScreen>
    )
  }

  // Confirmación tras enviar el pedido: el gate decide el mensaje (mozo vs cocina).
  if (submitOrder.isSuccess && submitOrder.data) {
    const gated = submitOrder.data.requires_confirmation
    return (
      <StateScreen
        title={t("publicMenu.sent.title")}
        action={
          <Button
            onClick={() => {
              submitOrder.reset()
              setCart({})
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

  const selfOrderEnabled = data.self_order_enabled === true
  const categories = data.categories.filter((c) => c.items.length > 0)

  // Índice id→ítem para resumir el carrito (nombre/precio) sin re-buscar.
  const itemsById = new Map<string, PublicMenuItemDTO>()
  for (const category of data.categories) {
    for (const item of category.items) itemsById.set(item.id, item)
  }

  const cartLines = Object.entries(cart).filter(([, qty]) => qty > 0)
  const cartCount = cartLines.reduce((n, [, qty]) => n + qty, 0)
  const cartTotal = cartLines.reduce((sum, [id, qty]) => {
    const item = itemsById.get(id)
    return sum + (item ? item.price_amount * qty : 0)
  }, 0)
  const showSend = selfOrderEnabled && cartCount > 0

  const setQty = (id: string, qty: number) =>
    setCart((prev) => {
      const next = { ...prev }
      if (qty <= 0) delete next[id]
      else next[id] = qty
      return next
    })

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
    submitOrder.mutate(
      cartLines.map(([product_id, quantity]) => ({ product_id, quantity })),
      {
        onError: (e) => {
          const unavailable = isApiError(e) && e.code === "product_unavailable"
          toast.error(
            t(unavailable ? "publicMenu.toast.orderUnavailable" : "publicMenu.toast.orderFailed")
          )
        },
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

      <main className={cn("mx-auto max-w-xl px-5 pt-6", showSend ? "pb-40" : "pb-28")}>
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
                currency={data.currency}
                fallbackLabel={t("publicMenu.uncategorized")}
                selfOrderEnabled={selfOrderEnabled}
                cart={cart}
                onQtyChange={setQty}
              />
            ))}
          </div>
        )}
        <p className="mt-10 text-center text-xs text-muted-foreground">
          {t("publicMenu.poweredBy")}
        </p>
      </main>

      {/* Barra fija: enviar el pedido (si hay carrito) + avisar al salón. */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-border/60 bg-background/90 px-5 py-3 backdrop-blur-xl">
        <div className="mx-auto flex max-w-xl flex-col gap-3">
          {showSend ? (
            <Button
              className="w-full justify-between"
              onClick={onSubmitOrder}
              disabled={submitOrder.isPending}
            >
              <span>
                {submitOrder.isPending
                  ? t("publicMenu.cart.sending")
                  : `${t("publicMenu.cart.send")} · ${cartCount}`}
              </span>
              <span className="tabular-nums">{formatMoney(cartTotal, data.currency)}</span>
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
            <Button
              variant={showSend ? "outline" : "default"}
              className="flex-1"
              onClick={onRequestBill}
              disabled={requestBill.isPending}
            >
              {t("publicMenu.actions.requestBill")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function MenuSection({
  category,
  currency,
  fallbackLabel,
  selfOrderEnabled,
  cart,
  onQtyChange,
}: {
  category: PublicMenuCategoryDTO
  currency: string
  fallbackLabel: string
  selfOrderEnabled: boolean
  cart: Record<string, number>
  onQtyChange: (id: string, qty: number) => void
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
          const qty = cart[item.id] ?? 0
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
                  <QtyStepper
                    qty={qty}
                    onDecrease={() => onQtyChange(item.id, qty - 1)}
                    onIncrease={() => onQtyChange(item.id, qty + 1)}
                  />
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
