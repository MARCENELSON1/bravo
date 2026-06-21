import { useState } from "react"
import { AlertTriangle } from "lucide-react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { IngredientDTO, UnitOfMeasure } from "@/api/types-inventory"
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
import {
  useCreateIngredient,
  useFoodCost,
  useIngredients,
  useLowStock,
  usePurchase,
  useWaste,
} from "@/hooks/use-inventory"
import { formatMoney } from "@/lib/money"
import { formatBps, formatQty, toMilesimas, UNIT_LABELS, UNIT_OPTIONS } from "@/lib/inventory"

// Alta de insumo. Internal (not exported) so the page file exports only the page.
function CreateIngredientSheet() {
  const create = useCreateIngredient()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [unit, setUnit] = useState<UnitOfMeasure>("KG")
  const [stock, setStock] = useState("")
  const [min, setMin] = useState("")
  const [cost, setCost] = useState("")

  const submit = () => {
    if (!name.trim()) {
      toast.error("Ingresá un nombre.")
      return
    }
    const unitCost = Math.round(Number(cost) * 100)
    if (!Number.isFinite(unitCost) || unitCost < 1) {
      toast.error("Ingresá un costo válido.")
      return
    }
    create.mutate(
      {
        name: name.trim(),
        unit,
        stock_qty: stock ? toMilesimas(stock) : 0,
        min_qty: min ? toMilesimas(min) : 0,
        unit_cost_amount: unitCost,
      },
      {
        onSuccess: () => {
          toast.success("Insumo creado.")
          setName("")
          setStock("")
          setMin("")
          setCost("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos crear el insumo."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button>Nuevo insumo</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Nuevo insumo</SheetTitle>
          <SheetDescription>
            El costo es por unidad base; el stock y el mínimo, en esa misma unidad.
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input placeholder="Nombre" value={name} onChange={(e) => setName(e.target.value)} />
          <Select value={unit} onValueChange={(v) => setUnit(v as UnitOfMeasure)}>
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
          <div className="flex gap-2">
            <Input
              type="number"
              step="0.001"
              min={0}
              placeholder={`Stock (${UNIT_LABELS[unit]})`}
              value={stock}
              onChange={(e) => setStock(e.target.value)}
            />
            <Input
              type="number"
              step="0.001"
              min={0}
              placeholder={`Mínimo (${UNIT_LABELS[unit]})`}
              value={min}
              onChange={(e) => setMin(e.target.value)}
            />
          </div>
          <Input
            type="number"
            step="0.01"
            min={0}
            placeholder={`Costo por ${UNIT_LABELS[unit]}`}
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? "Creando…" : "Crear insumo"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function PurchaseSheet({ ingredient }: { ingredient: IngredientDTO }) {
  const purchase = usePurchase()
  const [open, setOpen] = useState(false)
  const [qty, setQty] = useState("")
  const [cost, setCost] = useState("")

  const submit = () => {
    const q = qty ? toMilesimas(qty) : 0
    const unitCost = Math.round(Number(cost) * 100)
    if (q < 1) {
      toast.error("Ingresá una cantidad válida.")
      return
    }
    if (!Number.isFinite(unitCost) || unitCost < 1) {
      toast.error("Ingresá un costo válido.")
      return
    }
    purchase.mutate(
      { id: ingredient.id, body: { qty: q, unit_cost_amount: unitCost } },
      {
        onSuccess: () => {
          toast.success("Compra registrada.")
          setQty("")
          setCost("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar la compra."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          Comprar
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Comprar {ingredient.name}</SheetTitle>
          <SheetDescription>Suma stock y actualiza el costo (último costo).</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            type="number"
            step="0.001"
            min={0}
            placeholder={`Cantidad (${UNIT_LABELS[ingredient.unit]})`}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <Input
            type="number"
            step="0.01"
            min={0}
            placeholder={`Costo por ${UNIT_LABELS[ingredient.unit]}`}
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
          <Button onClick={submit} disabled={purchase.isPending}>
            {purchase.isPending ? "Guardando…" : "Registrar compra"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function WasteSheet({ ingredient }: { ingredient: IngredientDTO }) {
  const waste = useWaste()
  const [open, setOpen] = useState(false)
  const [qty, setQty] = useState("")
  const [note, setNote] = useState("")

  const submit = () => {
    const q = qty ? toMilesimas(qty) : 0
    if (q < 1) {
      toast.error("Ingresá una cantidad válida.")
      return
    }
    waste.mutate(
      { id: ingredient.id, body: { qty: q, note: note.trim() || null } },
      {
        onSuccess: () => {
          toast.success("Merma registrada.")
          setQty("")
          setNote("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos registrar la merma."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          Merma
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Merma de {ingredient.name}</SheetTitle>
          <SheetDescription>Baja stock por rotura, vencimiento o desperdicio.</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            type="number"
            step="0.001"
            min={0}
            placeholder={`Cantidad (${UNIT_LABELS[ingredient.unit]})`}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <Input
            placeholder="Motivo (opcional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button onClick={submit} disabled={waste.isPending}>
            {waste.isPending ? "Guardando…" : "Registrar merma"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function FoodCostSection() {
  const report = useFoodCost()
  if (report.isPending) return null
  if (!report.data || report.data.rows.length === 0) return null
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-foreground">Food cost por producto</h2>
      <div className="overflow-hidden rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead className="text-right">Precio</TableHead>
              <TableHead className="text-right">Food cost</TableHead>
              <TableHead className="text-right">Margen</TableHead>
              <TableHead className="text-right">% food cost</TableHead>
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
  const ingredients = useIngredients()
  const lowStock = useLowStock()
  const lowCount = lowStock.data?.length ?? 0

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Stock
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            Insumos, costo y alertas de quiebre. Vender descuenta según la receta.
          </p>
        </div>
        <CreateIngredientSheet />
      </header>

      {lowCount > 0 ? (
        <div className="flex items-start gap-3 rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
          <div>
            <p className="font-medium text-foreground">
              {lowCount} insumo{lowCount === 1 ? "" : "s"} en quiebre
            </p>
            <p className="text-muted-foreground">
              {lowStock.data?.map((i) => i.name).join(", ")}
            </p>
          </div>
        </div>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">Insumos</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {ingredients.isPending ? (
            <div className="flex justify-center p-10">
              <Spinner className="size-5 text-muted-foreground" />
            </div>
          ) : ingredients.data && ingredients.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Insumo</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Mínimo</TableHead>
                  <TableHead className="text-right">Costo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
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
                    <TableCell>
                      {i.is_below_min ? (
                        <Badge variant="destructive">Quiebre</Badge>
                      ) : (
                        <Badge variant="secondary">OK</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <PurchaseSheet ingredient={i} />
                        <WasteSheet ingredient={i} />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-8 text-center text-sm text-muted-foreground">
              Todavía no cargaste insumos.
            </p>
          )}
        </div>
      </section>

      <FoodCostSection />
    </div>
  )
}
