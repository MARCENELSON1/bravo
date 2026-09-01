import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { ModifierGroupDTO, ProductDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  draftsToInput,
  emptyGroup,
  emptyOption,
  groupsAreValid,
  toDrafts,
  type GroupDraft,
} from "@/features/products/modifiers-form"
import { useProductModifiers, useSetProductModifiers } from "@/hooks/use-products"

// Editor de modificadores del dueño (Carta QR F2 E parte 2). Replace-all contra
// PUT /products/{id}/modifiers, espejando el patrón de la receta.
export function ModifiersSheet({ product }: { product: ProductDTO }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("products.modifiers.button")}
        </Button>
      </SheetTrigger>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{t("products.modifiers.sheetTitle", { name: product.name })}</SheetTitle>
          <SheetDescription>{t("products.modifiers.sheetDescription")}</SheetDescription>
        </SheetHeader>
        {open ? <ModifiersEditor product={product} onDone={() => setOpen(false)} /> : null}
      </SheetContent>
    </Sheet>
  )
}

function ModifiersEditor({ product, onDone }: { product: ProductDTO; onDone: () => void }) {
  const modifiers = useProductModifiers(product.id)
  if (modifiers.isPending) {
    return (
      <div className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </div>
    )
  }
  return (
    <ModifiersForm
      productId={product.id}
      initialGroups={modifiers.data?.groups ?? []}
      onDone={onDone}
    />
  )
}

function ModifiersForm({
  productId,
  initialGroups,
  onDone,
}: {
  productId: string
  initialGroups: ModifierGroupDTO[]
  onDone: () => void
}) {
  const { t } = useTranslation()
  const setModifiers = useSetProductModifiers()
  const [groups, setGroups] = useState<GroupDraft[]>(() => toDrafts(initialGroups))

  const patchGroup = (gi: number, patch: Partial<GroupDraft>) =>
    setGroups((prev) => prev.map((g, i) => (i === gi ? { ...g, ...patch } : g)))
  const patchOption = (gi: number, oi: number, patch: Partial<GroupDraft["options"][number]>) =>
    setGroups((prev) =>
      prev.map((g, i) =>
        i === gi
          ? { ...g, options: g.options.map((o, j) => (j === oi ? { ...o, ...patch } : o)) }
          : g
      )
    )

  const save = () =>
    setModifiers.mutate(
      { productId, groups: draftsToInput(groups) },
      {
        onSuccess: () => {
          toast.success(t("products.modifiers.saved"))
          onDone()
        },
        onError: (error) => toast.error(apiErrorText(error, t, t("products.modifiers.saveError"))),
      }
    )

  return (
    <div className="flex flex-col gap-4 px-4 pb-4">
      {groups.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">
          {t("products.modifiers.empty")}
        </p>
      ) : (
        groups.map((group, gi) => (
          <div key={gi} className="flex flex-col gap-3 rounded-xl border border-border/60 p-3">
            <div className="flex items-center gap-2">
              <Input
                value={group.name}
                placeholder={t("products.modifiers.groupNamePlaceholder")}
                onChange={(e) => patchGroup(gi, { name: e.target.value })}
                className="h-9"
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 shrink-0"
                aria-label={t("products.modifiers.removeGroup")}
                onClick={() => setGroups((prev) => prev.filter((_, i) => i !== gi))}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <label className="flex items-center gap-1.5">
                <span className="text-muted-foreground">{t("products.modifiers.min")}</span>
                <Input
                  type="number"
                  min={0}
                  value={group.min}
                  onChange={(e) => patchGroup(gi, { min: e.target.value })}
                  className="h-8 w-16"
                />
              </label>
              <label className="flex items-center gap-1.5">
                <span className="text-muted-foreground">{t("products.modifiers.max")}</span>
                <Input
                  type="number"
                  min={1}
                  value={group.max}
                  onChange={(e) => patchGroup(gi, { max: e.target.value })}
                  className="h-8 w-16"
                />
              </label>
              <span className="text-xs text-muted-foreground">
                {t("products.modifiers.requiredHint")}
              </span>
            </div>

            <div className="flex flex-col gap-2">
              {group.options.map((option, oi) => (
                <div key={oi} className="flex items-center gap-2">
                  <Input
                    value={option.name}
                    placeholder={t("products.modifiers.optionNamePlaceholder")}
                    onChange={(e) => patchOption(gi, oi, { name: e.target.value })}
                    className="h-8 flex-1"
                  />
                  <Input
                    type="number"
                    step="0.01"
                    inputMode="decimal"
                    value={option.price}
                    placeholder={t("products.modifiers.optionPricePlaceholder")}
                    onChange={(e) => patchOption(gi, oi, { price: e.target.value })}
                    className="h-8 w-24"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    aria-label={t("products.modifiers.removeOption")}
                    onClick={() =>
                      patchGroup(gi, { options: group.options.filter((_, j) => j !== oi) })
                    }
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                className="self-start"
                onClick={() => patchGroup(gi, { options: [...group.options, emptyOption()] })}
              >
                <Plus className="mr-1 size-4" />
                {t("products.modifiers.addOption")}
              </Button>
            </div>
          </div>
        ))
      )}

      <Button
        variant="outline"
        className="self-start"
        onClick={() => setGroups((prev) => [...prev, emptyGroup()])}
      >
        <Plus className="mr-1 size-4" />
        {t("products.modifiers.addGroup")}
      </Button>

      <Button
        onClick={save}
        disabled={setModifiers.isPending || (groups.length > 0 && !groupsAreValid(groups))}
      >
        {setModifiers.isPending ? t("products.modifiers.saving") : t("products.modifiers.save")}
      </Button>
    </div>
  )
}
