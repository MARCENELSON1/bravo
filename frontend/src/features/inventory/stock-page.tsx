import { useState } from "react"
import { useTranslation } from "react-i18next"
import { AlertTriangle } from "lucide-react"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { IngredientDTO, UnitOfMeasure } from "@/api/types-inventory"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
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
import {
  useCreateIngredient,
  useFoodCost,
  useIngredients,
  useLowStock,
  usePurchase,
  useSuppliers,
  useUpdateIngredient,
  useWaste,
} from "@/hooks/use-inventory"
import { formatMoney } from "@/lib/money"
import {
  bpsToPercent,
  formatBps,
  formatQty,
  isValidYieldBps,
  percentToBps,
  recipeUnitOptions,
  toMilesimas,
  UNIT_LABELS,
  UNIT_OPTIONS,
} from "@/lib/inventory"

// Alta de insumo. Internal (not exported) so the page file exports only the page.
function CreateIngredientSheet() {
  const { t } = useTranslation()
  const create = useCreateIngredient()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [unit, setUnit] = useState<UnitOfMeasure>("KG")
  const [stock, setStock] = useState("")
  const [min, setMin] = useState("")
  const [cost, setCost] = useState("")
  const [yieldPct, setYieldPct] = useState("100")
  const [inclVat, setInclVat] = useState(true)
  // Fase 2C: "" = receta en la unidad base (sin conversión). Solo se setea al crear.
  const [recipeUnit, setRecipeUnit] = useState<UnitOfMeasure | "">("")
  const recipeOpts = recipeUnitOptions(unit)

  const submit = () => {
    if (!name.trim()) {
      toast.error(t("inventory.stock.invalidName"))
      return
    }
    const unitCost = Math.round(Number(cost) * 100)
    if (!Number.isFinite(unitCost) || unitCost < 1) {
      toast.error(t("inventory.stock.invalidCost"))
      return
    }
    const yp = yieldPct ? percentToBps(yieldPct) : 10000
    if (!isValidYieldBps(yp)) {
      toast.error(t("inventory.stock.invalidYield"))
      return
    }
    create.mutate(
      {
        name: name.trim(),
        unit,
        stock_qty: stock ? toMilesimas(stock) : 0,
        min_qty: min ? toMilesimas(min) : 0,
        unit_cost_amount: unitCost,
        yield_pct: yp,
        price_includes_tax: inclVat,
        recipe_unit: recipeUnit && recipeUnit !== unit ? recipeUnit : undefined,
      },
      {
        onSuccess: () => {
          toast.success(t("inventory.stock.createSuccess"))
          setName("")
          setStock("")
          setMin("")
          setCost("")
          setYieldPct("100")
          setInclVat(true)
          setRecipeUnit("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("inventory.stock.createError"))),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button>{t("inventory.stock.newIngredient")}</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("inventory.stock.createTitle")}</SheetTitle>
          <SheetDescription>{t("inventory.stock.createDescription")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            placeholder={t("inventory.stock.namePlaceholder")}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Select
            value={unit}
            onValueChange={(v) => {
              setUnit(v as UnitOfMeasure)
              setRecipeUnit("")  // otra familia → resetear la unidad de receta
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {UNIT_OPTIONS.map((u) => (
                <SelectItem key={u.value} value={u.value}>
                  {u.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {recipeOpts.length > 0 ? (
            <label className="flex flex-col gap-1 text-sm">
              {t("inventory.stock.recipeUnitLabel")}
              <Select
                value={recipeUnit || unit}
                onValueChange={(v) => setRecipeUnit(v as UnitOfMeasure)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {recipeOpts.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-xs text-muted-foreground">
                {t("inventory.stock.recipeUnitHint", {
                  base: UNIT_LABELS[unit],
                  recipe: UNIT_LABELS[recipeOpts[1].value],
                })}
              </span>
            </label>
          ) : null}
          <div className="flex gap-2">
            <Input
              type="number"
              step="0.001"
              min={0}
              placeholder={t("inventory.stock.stockPlaceholder", { unit: UNIT_LABELS[unit] })}
              value={stock}
              onChange={(e) => setStock(e.target.value)}
            />
            <Input
              type="number"
              step="0.001"
              min={0}
              placeholder={t("inventory.stock.minPlaceholder", { unit: UNIT_LABELS[unit] })}
              value={min}
              onChange={(e) => setMin(e.target.value)}
            />
          </div>
          <Input
            type="number"
            step="0.01"
            min={0}
            placeholder={t("inventory.stock.costPlaceholder", { unit: UNIT_LABELS[unit] })}
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
          <label className="flex flex-col gap-1 text-sm">
            {t("inventory.stock.yieldLabel")}
            <Input
              type="number"
              step="1"
              min={1}
              max={100}
              value={yieldPct}
              onChange={(e) => setYieldPct(e.target.value)}
            />
            <span className="text-xs text-muted-foreground">
              {t("inventory.stock.yieldHintCreate")}
            </span>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={inclVat}
              onChange={(e) => setInclVat(e.target.checked)}
            />
            {t("inventory.stock.vatCreate")}
          </label>
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? t("inventory.stock.creating") : t("inventory.stock.createSubmit")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function PurchaseSheet({ ingredient }: { ingredient: IngredientDTO }) {
  const { t } = useTranslation()
  const purchase = usePurchase()
  const suppliers = useSuppliers()
  const [open, setOpen] = useState(false)
  const [qty, setQty] = useState("")
  const [cost, setCost] = useState("")
  const [supplierId, setSupplierId] = useState("")
  // Tri-estado: `undefined` = "no tocar la clasificación de IVA del insumo" (una
  // compra no reclasifica). Solo se envía si el usuario la cambia en esta compra;
  // así una compra no revierte una reclasificación hecha en Editar. Se muestra la
  // clasificación vigente del insumo (prop fresca) mientras no se toque.
  const [inclVat, setInclVat] = useState<boolean | undefined>(undefined)
  const shownInclVat = inclVat ?? ingredient.cost_includes_tax

  const submit = () => {
    const q = qty ? toMilesimas(qty) : 0
    const unitCost = Math.round(Number(cost) * 100)
    if (q < 1) {
      toast.error(t("inventory.stock.invalidQty"))
      return
    }
    if (!Number.isFinite(unitCost) || unitCost < 1) {
      toast.error(t("inventory.stock.invalidCost"))
      return
    }
    purchase.mutate(
      {
        id: ingredient.id,
        body: {
          qty: q,
          unit_cost_amount: unitCost,
          ...(inclVat !== undefined ? { price_includes_tax: inclVat } : {}),
          ...(supplierId ? { supplier_id: supplierId } : {}),
        },
      },
      {
        onSuccess: () => {
          toast.success(t("inventory.stock.buySuccess"))
          setQty("")
          setCost("")
          setInclVat(undefined)
          setSupplierId("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("inventory.stock.buyError"))),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("inventory.stock.buy")}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("inventory.stock.buyTitle", { name: ingredient.name })}</SheetTitle>
          <SheetDescription>{t("inventory.stock.buyDescription")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            type="number"
            step="0.001"
            min={0}
            placeholder={t("inventory.stock.qtyPlaceholder", {
              unit: UNIT_LABELS[ingredient.unit],
            })}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <Input
            type="number"
            step="0.01"
            min={0}
            placeholder={t("inventory.stock.costPlaceholder", {
              unit: UNIT_LABELS[ingredient.unit],
            })}
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
          <select
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
          >
            <option value="">{t("inventory.stock.supplierOption")}</option>
            {(suppliers.data ?? [])
              .filter((s) => s.active)
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={shownInclVat}
              onChange={(e) => setInclVat(e.target.checked)}
            />
            {t("inventory.stock.vatBuy")}
          </label>
          <Button onClick={submit} disabled={purchase.isPending}>
            {purchase.isPending ? t("inventory.stock.saving") : t("inventory.stock.buySubmit")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function WasteSheet({ ingredient }: { ingredient: IngredientDTO }) {
  const { t } = useTranslation()
  const waste = useWaste()
  const [open, setOpen] = useState(false)
  const [qty, setQty] = useState("")
  const [note, setNote] = useState("")

  const submit = () => {
    const q = qty ? toMilesimas(qty) : 0
    if (q < 1) {
      toast.error(t("inventory.stock.invalidQty"))
      return
    }
    waste.mutate(
      { id: ingredient.id, body: { qty: q, note: note.trim() || null } },
      {
        onSuccess: () => {
          toast.success(t("inventory.stock.wasteSuccess"))
          setQty("")
          setNote("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("inventory.stock.wasteError"))),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("inventory.stock.waste")}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("inventory.stock.wasteTitle", { name: ingredient.name })}</SheetTitle>
          <SheetDescription>{t("inventory.stock.wasteDescription")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            type="number"
            step="0.001"
            min={0}
            placeholder={t("inventory.stock.qtyPlaceholder", {
              unit: UNIT_LABELS[ingredient.unit],
            })}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <Input
            placeholder={t("inventory.stock.wasteNotePlaceholder")}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button onClick={submit} disabled={waste.isPending}>
            {waste.isPending ? t("inventory.stock.saving") : t("inventory.stock.wasteSubmit")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

// Editar un insumo existente: nombre + rendimiento (merma). El costo se mueve
// por compras (último costo), no acá.
// Seeds its state from props at mount; the sheet renders it only while open, so
// it remounts (re-seeds from fresh server data) each time — no stale lost-update.
function EditIngredientForm({
  ingredient,
  onDone,
}: {
  ingredient: IngredientDTO
  onDone: () => void
}) {
  const { t } = useTranslation()
  const update = useUpdateIngredient()
  const [name, setName] = useState(ingredient.name)
  const [yieldPct, setYieldPct] = useState(String(bpsToPercent(ingredient.yield_pct)))
  const [inclVat, setInclVat] = useState(ingredient.cost_includes_tax)

  const submit = () => {
    const yp = percentToBps(yieldPct)
    if (!isValidYieldBps(yp)) {
      toast.error(t("inventory.stock.invalidYield"))
      return
    }
    update.mutate(
      {
        id: ingredient.id,
        body: { name: name.trim() || undefined, yield_pct: yp, cost_includes_tax: inclVat },
      },
      {
        onSuccess: () => {
          toast.success(t("inventory.stock.updateSuccess"))
          onDone()
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("inventory.stock.updateError"))),
      }
    )
  }

  return (
    <div className="flex flex-col gap-3 px-4 pb-4">
      <Input
        placeholder={t("inventory.stock.namePlaceholder")}
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <label className="flex flex-col gap-1 text-sm">
        {t("inventory.stock.yieldLabel")}
        <Input
          type="number"
          step="1"
          min={1}
          max={100}
          value={yieldPct}
          onChange={(e) => setYieldPct(e.target.value)}
        />
        <span className="text-xs text-muted-foreground">
          {t("inventory.stock.yieldHintEdit")}
        </span>
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={inclVat}
          onChange={(e) => setInclVat(e.target.checked)}
        />
        {t("inventory.stock.vatEdit")}
      </label>
      <Button onClick={submit} disabled={update.isPending}>
        {update.isPending ? t("inventory.stock.saving") : t("inventory.stock.save")}
      </Button>
    </div>
  )
}

function EditIngredientSheet({ ingredient }: { ingredient: IngredientDTO }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("inventory.stock.edit")}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("inventory.stock.editTitle", { name: ingredient.name })}</SheetTitle>
          <SheetDescription>{t("inventory.stock.editDescription")}</SheetDescription>
        </SheetHeader>
        {open ? (
          <EditIngredientForm ingredient={ingredient} onDone={() => setOpen(false)} />
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

function FoodCostSection() {
  const { t } = useTranslation()
  const report = useFoodCost()
  if (report.isPending) return null
  if (!report.data || report.data.rows.length === 0) return null
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-foreground">{t("inventory.stock.foodCostTitle")}</h2>
      <div className="overflow-hidden rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("inventory.stock.foodCostColumns.product")}</TableHead>
              <TableHead className="text-right">{t("inventory.stock.foodCostColumns.price")}</TableHead>
              <TableHead className="text-right">{t("inventory.stock.foodCostColumns.foodCost")}</TableHead>
              <TableHead className="text-right">{t("inventory.stock.foodCostColumns.margin")}</TableHead>
              <TableHead className="text-right">{t("inventory.stock.foodCostColumns.foodCostPct")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.data.rows.map((r) => (
              <TableRow key={r.product_id}>
                <TableCell className="font-medium">{r.product_name}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(r.price_amount, r.currency)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(r.food_cost_amount, r.currency)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  <span className={r.margin_amount < 0 ? "text-destructive" : undefined}>
                    {formatMoney(r.margin_amount, r.currency)}
                  </span>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatBps(r.food_cost_ratio_bps)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  )
}

export function StockPage() {
  const { t } = useTranslation()
  const ingredients = useIngredients()
  const lowStock = useLowStock()
  const lowCount = lowStock.data?.length ?? 0

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("inventory.stock.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            {t("inventory.stock.subtitle")}
          </p>
        </div>
        <CreateIngredientSheet />
      </header>

      {lowCount > 0 ? (
        <div className="flex items-start gap-3 rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
          <div>
            <p className="font-medium text-foreground">
              {t("inventory.stock.lowStock", { count: lowCount })}
            </p>
            <p className="text-muted-foreground">
              {lowStock.data?.map((i) => i.name).join(", ")}
            </p>
          </div>
        </div>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">{t("inventory.stock.sectionTitle")}</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {ingredients.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : ingredients.data && ingredients.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("inventory.stock.columns.ingredient")}</TableHead>
                  <TableHead className="text-right">{t("inventory.stock.columns.stock")}</TableHead>
                  <TableHead className="text-right">{t("inventory.stock.columns.min")}</TableHead>
                  <TableHead className="text-right">{t("inventory.stock.columns.cost")}</TableHead>
                  <TableHead className="text-right">{t("inventory.stock.columns.yield")}</TableHead>
                  <TableHead>{t("inventory.stock.columns.status")}</TableHead>
                  <TableHead className="text-right">{t("inventory.stock.columns.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ingredients.data.map((i) => (
                  <TableRow key={i.id}>
                    <TableCell className="font-medium">{i.name}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatQty(i.stock_qty, i.unit)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-muted-foreground">
                      {formatQty(i.min_qty, i.unit)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(i.unit_cost_amount, i.currency)} / {UNIT_LABELS[i.unit]}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-muted-foreground">
                      {bpsToPercent(i.yield_pct)}%
                    </TableCell>
                    <TableCell>
                      {i.is_below_min ? (
                        <Badge variant="destructive">{t("inventory.stock.statusBreak")}</Badge>
                      ) : (
                        <Badge variant="secondary">{t("inventory.stock.statusOk")}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <EditIngredientSheet ingredient={i} />
                        <PurchaseSheet ingredient={i} />
                        <WasteSheet ingredient={i} />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState>
              {t("inventory.stock.emptyState")}
            </EmptyState>
          )}
        </div>
      </section>

      <FoodCostSection />
    </div>
  )
}
