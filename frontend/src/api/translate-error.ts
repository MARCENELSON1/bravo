import type { TFunction } from "i18next"

import { isApiError } from "@/api/api-error"

/**
 * Texto de error para mostrar, traducido por el `code` ESTABLE del backend
 * (no por el `message`, que viene en español).
 *
 * - Si es un `ApiError`: busca `errors.<code>` en el diccionario del idioma
 *   actual. Si ese code no está traducido, cae al `message` (español) del
 *   backend vía `defaultValue` → degradación elegante y paridad AR garantizada.
 * - Si NO es un `ApiError` (error de red, excepción inesperada): usa `fallback`.
 *
 * Reemplaza el patrón `isApiError(e) ? e.message : "…"` para que el error se
 * muestre en el idioma de la UI cuando hay traducción.
 */
export function apiErrorText(error: unknown, t: TFunction, fallback: string): string {
  if (isApiError(error)) {
    return t(`errors.${error.code}`, { defaultValue: error.message })
  }
  return fallback
}
