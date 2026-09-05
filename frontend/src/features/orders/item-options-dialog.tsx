import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"

import type {
  ModifierGroupDTO,
  ProductDTO,
  SelectedOptionDTO,
} from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { formatMoney } from "@/lib/money"
import { optionsDelta, selectionValid, snapshotOptions, toggleOption } from "@/lib/modifiers"

export interface ItemOptionsResult {
  quantity: number
  note: string | null
  optionIds: string[]
  selectedOptions: SelectedOptionDTO[]
}

/**
 * "Cómo se quiere el plato": modificadores estructurados (chips por grupo, con
 * su regla y el delta de precio) + cantidad + nota para cocina. Se abre al
 * tocar un producto con un grupo obligatorio, o desde el ✎ de la tarjeta.
 * "Agregar" queda deshabilitado hasta cumplir la regla de cada grupo.
 */
export function ItemOptionsDialog({
  product,
  groups,
  open,
  onOpenChange,
  onConfirm,
}: {
  product: ProductDTO
  groups: ModifierGroupDTO[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (result: ItemOptionsResult) => void
}) {
  const { t } = useTranslation()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [note, setNote] = useState("")
  const [quantity, setQuantity] = useState(1)

  const delta = useMemo(() => optionsDelta(groups, selected), [groups, selected])
  const valid = selectionValid(groups, selected)

  const toggle = (group: ModifierGroupDTO, optionId: string) => {
    setSelected((prev) => toggleOption(group, optionId, prev))
  }

  const confirm = () => {
    const trimmed = note.trim()
    onConfirm({
      quantity,
      note: trimmed === "" ? null : trimmed,
      optionIds: [...selected],
      selectedOptions: snapshotOptions(groups, selected),
    })
    setSelected(new Set())
    setNote("")
    setQuantity(1)
    onOpenChange(false)
  }

  const groupRule = (group: ModifierGroupDTO): string =>
    group.required
      ? group.max_select === 1
        ? t("orders.options.pickOne")
        : t("orders.options.atLeast", { count: group.min_select })
      : t("orders.options.upTo", { count: group.max_select })

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{product.name}</SheetTitle>
          <SheetDescription>
            {formatMoney(product.price_amount + delta, product.currency)}
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 py-2">
          {groups.map((group) => (
            <div key={group.id} className="flex flex-col gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium">{group.name}</span>
                <span
                  className={
                    group.required
                      ? "text-xs font-medium text-primary"
                      : "text-xs text-muted-foreground"
                  }
                >
                  {groupRule(group)}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {group.options.map((option) => {
                  const on = selected.has(option.id)
                  return (
                    <Button
                      key={option.id}
                      type="button"
                      variant={on ? "default" : "outline"}
                      className="h-9"
                      onClick={() => toggle(group, option.id)}
                    >
                      {option.name}
                      {option.price_delta > 0
                        ? ` +${formatMoney(option.price_delta, product.currency)}`
                        : ""}
                    </Button>
                  )
                })}
              </div>
            </div>
          ))}

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{t("orders.options.quantity")}</span>
            <Button
              variant="outline"
              className="h-9 w-9 p-0 text-lg"
              onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              aria-label={t("orders.lessQuantity")}
            >
              −
            </Button>
            <span className="w-7 text-center text-sm font-medium tabular-nums">{quantity}</span>
            <Button
              variant="outline"
              className="h-9 w-9 p-0 text-lg"
              onClick={() => setQuantity((q) => q + 1)}
              aria-label={t("orders.moreQuantity")}
            >
              +
            </Button>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium" htmlFor="item-note">
              {t("orders.options.noteLabel")}
            </label>
            <Input
              id="item-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={t("orders.options.notePlaceholder")}
            />
          </div>
        </div>

        <SheetFooter>
          <Button className="w-full" disabled={!valid} onClick={confirm}>
            {t("orders.options.add", { count: quantity })}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
