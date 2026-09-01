import { Minus, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type {
  PublicMenuCategoryDTO,
  PublicMenuItemDTO,
  PublicMenuModifierGroupDTO,
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
  usePublicMenu,
  useRequestBill,
  useSubmitCustomerOrder,
} from "@/hooks/use-public-menu"
import { formatMoney } from "@/lib/money"
import { cn } from "@/lib/utils"

// Carta pública de cara al comensal (ruta /carta/:token, SIN auth). Mobile-first,
// theme-aware. Con autopedido prendido (F2): carrito line-based (un ítem puede
// entrar con distintos modificadores) + picker de opciones + envío.
export function PublicMenuPage() {
  const { t } = useTranslation()
  const { token } = useParams<{ token: string }>()
  const { data, isLoading, isError, error } = usePublicMenu(token)
  const callWaiter = useCallWaiter(token)
  const requestBill = useRequestBill(token)
  const submitOrder = useSubmitCustomerOrder(token)
  const [cart, setCart] = useState<CartLine[]>([])
  const [picker, setPicker] = useState<PublicMenuItemDTO | null>(null)
  const [reviewOpen, setReviewOpen] = useState(false)

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
            <Button
              variant={showCartBar ? "outline" : "default"}
              className="flex-1"
              onClick={onRequestBill}
              disabled={requestBill.isPending}
            >
              {t("publicMenu.actions.requestBill")}
            </Button>
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
    </div>
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
