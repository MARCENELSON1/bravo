import type { RecipeItemDTO } from "@/api/types-inventory"
import { toMilesimas } from "@/lib/inventory"

// Helpers de edición de componentes de receta/preparación (Productos v2 Tanda C).
// Una fila codifica el componente elegido como "ing:<id>" | "prep:<id>" y su
// cantidad en la unidad (se convierte a milésimas al guardar).

export type ComponentDraft = { value: string; qty: string }

export const ING = "ing:"
export const PREP = "prep:"

export function itemsToDrafts(items: RecipeItemDTO[]): ComponentDraft[] {
  return items.map((i) => ({
    value: i.preparation_id ? PREP + i.preparation_id : ING + (i.ingredient_id ?? ""),
    qty: String(i.qty / 1000),
  }))
}

export function draftsToItems(rows: ComponentDraft[]): RecipeItemDTO[] {
  return rows
    .filter((r) => r.value && Number(r.qty) > 0)
    .map((r) =>
      r.value.startsWith(PREP)
        ? { preparation_id: r.value.slice(PREP.length), qty: toMilesimas(r.qty) }
        : { ingredient_id: r.value.slice(ING.length), qty: toMilesimas(r.qty) }
    )
}
