import type { ModifierGroupDTO, SelectedOptionDTO } from "@/api/types-operations"

// Modificadores estructurados ("cómo se quiere el plato"): chips por grupo con
// su regla min/max y su delta de precio. Espeja `capture_logic.dart` de mobile
// y `select_options` del backend, para que los tres validen lo mismo.

/**
 * Regla de cada grupo: un obligatorio sin elegir, o más opciones que su
 * `max_select`, invalidan la selección (el server responde 422).
 */
export function selectionValid(
  groups: ModifierGroupDTO[],
  selected: ReadonlySet<string>
): boolean {
  return groups.every((group) => {
    const n = group.options.filter((option) => selected.has(option.id)).length
    return n >= group.min_select && n <= group.max_select
  })
}

/** Snapshot (nombre + delta) de lo elegido, para pintar la línea optimista. */
export function snapshotOptions(
  groups: ModifierGroupDTO[],
  selected: ReadonlySet<string>
): SelectedOptionDTO[] {
  return groups.flatMap((group) =>
    group.options
      .filter((option) => selected.has(option.id))
      .map((option) => ({
        option_id: option.id,
        name: option.name,
        price_delta: option.price_delta,
      }))
  )
}

/** Suma de deltas: se pliega en el precio unitario (igual que el server). */
export function optionsDelta(
  groups: ModifierGroupDTO[],
  selected: ReadonlySet<string>
): number {
  return snapshotOptions(groups, selected).reduce((a, o) => a + o.price_delta, 0)
}

/**
 * Alterna una opción respetando la regla del grupo: elegir-uno reemplaza, y
 * multi-selección no pasa de `max_select`.
 */
export function toggleOption(
  group: ModifierGroupDTO,
  optionId: string,
  selected: ReadonlySet<string>
): Set<string> {
  const next = new Set(selected)
  if (group.max_select === 1) {
    for (const option of group.options) next.delete(option.id)
    next.add(optionId)
    return next
  }
  if (next.has(optionId)) {
    next.delete(optionId)
    return next
  }
  const chosen = group.options.filter((option) => next.has(option.id)).length
  if (chosen < group.max_select) next.add(optionId)
  return next
}

/** Tiene al menos un grupo obligatorio → al tocarlo hay que elegir primero. */
export function needsChoice(groups: ModifierGroupDTO[]): boolean {
  return groups.some((group) => group.required)
}
