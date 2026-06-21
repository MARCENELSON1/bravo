import type { UnitOfMeasure } from "@/api/types-inventory"

// Quantities are stored as integers in milésimas of the base unit.
export const QUANTITY_SCALE = 1000

export const UNIT_LABELS: Record<UnitOfMeasure, string> = {
  G: "g",
  KG: "kg",
  ML: "ml",
  L: "l",
  UNIT: "u",
}

export const UNIT_OPTIONS: { value: UnitOfMeasure; label: string }[] = [
  { value: "KG", label: "Kilogramos (kg)" },
  { value: "G", label: "Gramos (g)" },
  { value: "L", label: "Litros (l)" },
  { value: "ML", label: "Mililitros (ml)" },
  { value: "UNIT", label: "Unidades (u)" },
]

// milésimas → human (e.g. 1500, "KG" → "1,5 kg"). Negative stock is shown as-is.
export function formatQty(qty: number, unit: string): string {
  const value = qty / QUANTITY_SCALE
  const label = UNIT_LABELS[unit as UnitOfMeasure] ?? unit
  return `${value.toLocaleString("es-AR", { maximumFractionDigits: 3 })} ${label}`
}

// A decimal qty typed by the user (e.g. "1.5") → milésimas integer.
export function toMilesimas(value: string): number {
  return Math.round(Number(value) * QUANTITY_SCALE)
}

// Food cost ratio in basis points → percent label (e.g. 1067 → "10,7%").
export function formatBps(bps: number): string {
  return `${(bps / 100).toLocaleString("es-AR", { maximumFractionDigits: 1 })}%`
}
