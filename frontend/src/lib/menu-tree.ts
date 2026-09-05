// El backend guarda UNA categoría de texto libre por producto. Para conseguir un
// nivel más de agrupación sin tocar el back, se acuerda una convención: separar
// con "/" — "Bebidas / Cervezas" es la categoría "Bebidas" y la subcategoría
// "Cervezas". Es convención, no estructura: nada valida el formato, y lo que se
// cargue sin separador simplemente no tiene subcategoría.

export interface CategoryPath {
  /** Nivel 1. `null` si el producto no tiene categoría. */
  main: string | null
  /** Nivel 2. `null` si la categoría no usa el separador. */
  sub: string | null
}

const SEPARATOR = "/"

// "Bebidas / Cervezas / IPA" → { main: "Bebidas", sub: "Cervezas / IPA" }.
// Se corta solo en el primer separador: lo que sigue queda como un nombre de
// subcategoría, en vez de abrir niveles infinitos que la UI no muestra.
export function splitCategory(raw: string | null | undefined): CategoryPath {
  const value = raw?.trim()
  if (!value) return { main: null, sub: null }

  const at = value.indexOf(SEPARATOR)
  if (at === -1) return { main: value, sub: null }

  const main = value.slice(0, at).trim()
  const sub = value.slice(at + 1).trim()
  // "/ Cervezas" o "Bebidas /" están mal cargados: se usa lo que haya como nivel 1.
  if (!main) return { main: sub || null, sub: null }
  if (!sub) return { main, sub: null }
  return { main, sub }
}
