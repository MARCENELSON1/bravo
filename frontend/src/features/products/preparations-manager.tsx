import { useMemo, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { IngredientDTO, PreparationDTO } from "@/api/types-inventory"
import { Button } from "@/components/ui/button"
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
  type ComponentDraft,
  draftsToItems,
  ING,
  itemsToDrafts,
  PREP,
} from "@/features/products/recipe-items"
import {
  useCreatePreparation,
  useDeletePreparation,
  useIngredients,
  usePreparations,
  useUpdatePreparation,
} from "@/hooks/use-inventory"
import { toMilesimas, UNIT_LABELS } from "@/lib/inventory"

// Editor reutilizable de componentes (insumos + preparaciones). Lo usan la receta
// de un producto y la de una preparación.
export function ComponentRowsEditor({
  rows,
  onChange,
  ingredients,
  preparations,
}: {
  rows: ComponentDraft[]
  onChange: (rows: ComponentDraft[]) => void
  ingredients: IngredientDTO[]
  preparations: PreparationDTO[]
}) {
  const add = () => onChange([...rows, { value: "", qty: "" }])
  const remove = (index: number) => onChange(rows.filter((_, i) => i !== index))
  const patch = (index: number, patch: Partial<ComponentDraft>) =>
    onChange(rows.map((r, i) => (i === index ? { ...r, ...patch } : r)))

  return (
    <div className="flex flex-col gap-2">
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Sin componentes. Agregá insumos o preparaciones.
        </p>
      ) : null}
      {rows.map((row, index) => {
        // Fase 2C: la cantidad se tipea en la unidad de RECETA del insumo
        // (recipe_unit si está, si no la base) → mostrar la etiqueta correcta.
        const ing = row.value.startsWith(ING)
          ? ingredients.find((i) => i.id === row.value.slice(ING.length))
          : undefined
        const unitLabel = ing ? UNIT_LABELS[ing.recipe_unit ?? ing.unit] : ""
        return (
          <div key={index} className="flex items-end gap-2">
            <Select value={row.value} onValueChange={(v) => patch(index, { value: v })}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Insumo o preparación" />
              </SelectTrigger>
              <SelectContent>
                {ingredients.map((i) => (
                  <SelectItem key={i.id} value={ING + i.id}>
                    {i.name}
                  </SelectItem>
                ))}
                {preparations.map((p) => (
                  <SelectItem key={p.id} value={PREP + p.id}>
                    Preparación: {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="number"
              step="0.001"
              min={0}
              placeholder="cant."
              value={row.qty}
              onChange={(e) => patch(index, { qty: e.target.value })}
              className="max-w-[6rem]"
            />
            <span className="w-6 shrink-0 pb-2 text-xs text-muted-foreground">
              {unitLabel}
            </span>
            <Button variant="ghost" size="sm" onClick={() => remove(index)}>
              Quitar
            </Button>
          </div>
        )
      })}
      <Button variant="outline" size="sm" onClick={add}>
        Agregar componente
      </Button>
    </div>
  )
}

function PreparationForm({
  initial,
  ingredients,
  preparations,
  onDone,
}: {
  initial: PreparationDTO | null
  ingredients: IngredientDTO[]
  preparations: PreparationDTO[]
  onDone: () => void
}) {
  const create = useCreatePreparation()
  const update = useUpdatePreparation()
  const [name, setName] = useState(initial?.name ?? "")
  const [yieldQty, setYieldQty] = useState(() =>
    initial ? String(initial.yield_qty / 1000) : ""
  )
  const [rows, setRows] = useState<ComponentDraft[]>(() =>
    initial ? itemsToDrafts(initial.items) : []
  )
  // Una preparación no puede contenerse a sí misma (el ciclo indirecto lo corta el backend).
  const options = useMemo(
    () => preparations.filter((p) => p.id !== initial?.id),
    [preparations, initial?.id]
  )

  const pending = create.isPending || update.isPending

  const save = () => {
    const items = draftsToItems(rows)
    if (!name.trim() || Number(yieldQty) <= 0 || items.length === 0) {
      toast.error("Cargá nombre, rendimiento y al menos un componente.")
      return
    }
    const body = { name: name.trim(), yield_qty: toMilesimas(yieldQty), items }
    const onSuccess = () => {
      toast.success("Preparación guardada.")
      onDone()
    }
    const onError = (error: unknown) =>
      toast.error(isApiError(error) ? error.message : "No pudimos guardar la preparación.")
    if (initial) {
      update.mutate({ id: initial.id, body }, { onSuccess, onError })
    } else {
      create.mutate(body, { onSuccess, onError })
    }
  }

  if (ingredients.length === 0) {
    return (
      <p className="px-4 py-6 text-sm text-muted-foreground">
        Cargá insumos en Stock antes de armar una preparación.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4 px-4 pb-4">
      <label className="flex flex-col gap-1 text-sm">
        Nombre
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Salsa fileto" />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Rendimiento (cuánto rinde una tanda, en su unidad)
        <Input
          type="number"
          step="0.001"
          min={0}
          value={yieldQty}
          onChange={(e) => setYieldQty(e.target.value)}
          placeholder="Ej. 2 (= 2 kg / 2 L / 2 u)"
        />
      </label>
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium">Componentes</span>
        <ComponentRowsEditor
          rows={rows}
          onChange={setRows}
          ingredients={ingredients}
          preparations={options}
        />
      </div>
      <Button onClick={save} disabled={pending}>
        {pending ? "Guardando…" : "Guardar preparación"}
      </Button>
    </div>
  )
}

function PreparationSheet({
  initial,
  ingredients,
  preparations,
  trigger,
}: {
  initial: PreparationDTO | null
  ingredients: IngredientDTO[]
  preparations: PreparationDTO[]
  trigger: React.ReactNode
}) {
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>{trigger}</SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{initial ? `Editar ${initial.name}` : "Nueva preparación"}</SheetTitle>
          <SheetDescription>
            Una preparación base (receta madre) se usa dentro de varios platos; su costo
            se prorratea por lo que rinde.
          </SheetDescription>
        </SheetHeader>
        {open ? (
          <PreparationForm
            initial={initial}
            ingredients={ingredients}
            preparations={preparations}
            onDone={() => setOpen(false)}
          />
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

// Sección "Recetas madre" en la pantalla Productos.
export function PreparationsManager() {
  const preparations = usePreparations()
  const ingredients = useIngredients()
  const del = useDeletePreparation()

  const list = preparations.data ?? []
  const ings = ingredients.data ?? []

  const remove = (prep: PreparationDTO) => {
    if (!window.confirm(`¿Eliminar la preparación "${prep.name}"?`)) return
    del.mutate(prep.id, {
      onSuccess: () => toast.success("Preparación eliminada."),
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos eliminar la preparación."),
    })
  }

  return (
    <section className="flex flex-col gap-3">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-foreground">Recetas madre</h2>
          <p className="text-sm text-muted-foreground">
            Preparaciones base reutilizables (ej. salsa fileto). Se usan dentro de las
            recetas y su costo se propaga solo.
          </p>
        </div>
        <PreparationSheet
          initial={null}
          ingredients={ings}
          preparations={list}
          trigger={<Button variant="outline">Nueva preparación</Button>}
        />
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {preparations.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : list.length > 0 ? (
          <ul className="divide-y divide-border">
            {list.map((prep) => (
              <li key={prep.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">{prep.name}</p>
                  <p className="text-xs text-muted-foreground">
                    Rinde {prep.yield_qty / 1000} · {prep.items.length}{" "}
                    {prep.items.length === 1 ? "componente" : "componentes"} ·{" "}
                    {prep.used_in_products === 0
                      ? "sin usar"
                      : `usada en ${prep.used_in_products} ${
                          prep.used_in_products === 1 ? "plato" : "platos"
                        }`}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <PreparationSheet
                    initial={prep}
                    ingredients={ings}
                    preparations={list}
                    trigger={
                      <Button variant="ghost" size="sm">
                        Editar
                      </Button>
                    }
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove(prep)}
                    disabled={del.isPending}
                  >
                    Eliminar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="bg-black/[0.06] p-8 text-center text-sm font-medium text-muted-foreground dark:bg-white/[0.05]">
            Todavía no cargaste preparaciones.
          </p>
        )}
      </div>
    </section>
  )
}
