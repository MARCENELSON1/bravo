import type { ModifierGroupDTO, ModifierGroupInput } from "@/api/types-operations"

// Editor de modificadores (Carta QR F2 E parte 2). El precio se edita en unidades
// mayores (pesos) y se guarda en menores (centavos), como el form de producto.
export interface OptionDraft {
  name: string
  price: string // unidades mayores (ej. "3000"); vacío = 0
}

export interface GroupDraft {
  name: string
  min: string
  max: string
  options: OptionDraft[]
}

export function emptyOption(): OptionDraft {
  return { name: "", price: "" }
}

export function emptyGroup(): GroupDraft {
  return { name: "", min: "0", max: "1", options: [emptyOption()] }
}

export function toDrafts(groups: ModifierGroupDTO[]): GroupDraft[] {
  return groups.map((g) => ({
    name: g.name,
    min: String(g.min_select),
    max: String(g.max_select),
    options: g.options.map((o) => ({
      name: o.name,
      price: o.price_delta ? String(o.price_delta / 100) : "",
    })),
  }))
}

// Draft → payload del PUT. Descarta opciones sin nombre; precio pesos → centavos.
export function draftsToInput(drafts: GroupDraft[]): ModifierGroupInput[] {
  return drafts.map((g) => ({
    name: g.name.trim(),
    min_select: Math.max(0, Math.trunc(Number(g.min) || 0)),
    max_select: Math.max(1, Math.trunc(Number(g.max) || 1)),
    options: g.options
      .filter((o) => o.name.trim())
      .map((o) => ({
        name: o.name.trim(),
        price_delta: Math.max(0, Math.round((Number(o.price) || 0) * 100)),
      })),
  }))
}

// Validación de guardado (espeja las reglas del dominio, para avisar antes del 422).
export function groupsAreValid(drafts: GroupDraft[]): boolean {
  return drafts.every((g) => {
    const options = g.options.filter((o) => o.name.trim())
    const min = Math.trunc(Number(g.min) || 0)
    const max = Math.trunc(Number(g.max) || 1)
    return (
      g.name.trim().length > 0 &&
      options.length > 0 &&
      min >= 0 &&
      max >= 1 &&
      max >= min &&
      min <= options.length
    )
  })
}
