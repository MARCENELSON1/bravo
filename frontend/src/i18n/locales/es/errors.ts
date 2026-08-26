// Namespace `errors`: mensajes de error por `code` estable del backend.
//
// En español queda VACÍO a propósito: `apiErrorText` usa el `message` (español)
// que ya devuelve el backend como `defaultValue`. Así el usuario AR ve SIEMPRE el
// texto canónico del backend (paridad exacta, sin riesgo de divergencia). El
// inglés vive en `en/errors.ts`.
export const errors = {} as const
