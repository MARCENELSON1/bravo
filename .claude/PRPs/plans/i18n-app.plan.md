# PRP — i18n de la app (`app.wellnod.com`) — español ↔ inglés

> **Estado:** Hoja de ruta (NO codeado). Creado 2026-08-26.
> **Objetivo:** que un restaurante de EE.UU. use **toda la app en inglés** (no solo el login). Hoy la landing EN manda al usuario a una app en español → rompe el funnel US.
> **Relacionado:** `landing-internacional.plan.md` (la landing ya es bilingüe + geo), `plan-funnel-billing.md`.

---

## Estado actual (lo que YA está)

- **Infra i18n lista:** `src/i18n/index.ts` (react-i18next, init síncrono, recursos inline `es`/`en`), `pickInitialLang(saved, browserLang)` (elección persistida > navegador `en-*` > español), `setLanguage()` persiste en `localStorage` (`wellnod:lang`), default **español = paridad** (ningún usuario actual ve un cambio). `LanguageSwitcher` existe.
- **Errores de API tipados:** `src/api/api-error.ts` → `ApiError { code, message, status }`. El `code` es **inglés estable** (`invalid_credentials`), el `message` es **español** para mostrar.

## Estado actual (lo que FALTA)

- **Solo 1 de 54 pantallas migrada** (login). `src/i18n/locales/es.ts`/`en.ts` tienen solo `common` + `login`. **Las otras ~53 tienen el español hardcodeado.**
- **El panel izquierdo de auth** (`src/components/auth/auth-layout.tsx`, "El cerebro del local") está hardcodeado ES.
- **Los errores se muestran en español:** ~35 call-sites hacen `isApiError(error) ? error.message : "fallback"` → muestran el `message` español del backend, ignorando el idioma de la UI.

---

## Los DOS frentes

### Frente A — Migrar los strings del frontend a `t()`
Cada pantalla: `useTranslation()` + reemplazar strings hardcodeados por `t("area.clave")`. Los `es.ts`/`en.ts` crecen con un **namespace por feature**.

### Frente B — Traducir los errores por `code` (no por `message`)
Un helper compartido que traduce el error por su `code`, con el `message` del backend como fallback:
```ts
// src/api/translate-error.ts (nuevo)
export function apiErrorText(error: unknown, t: TFunction, fallback: string): string {
  if (isApiError(error)) return t(`errors.${error.code}`, { defaultValue: error.message })
  return fallback
}
```
- Se reemplazan los ~35 `isApiError(e) ? e.message : "…"` por `apiErrorText(e, t, "…")`.
- Se arma el diccionario **`errors.<code>`** en `es.ts`/`en.ts`. Los codes salen del backend (`app/presentation/errors.py` mapea excepción→code). Si un code no está traducido, cae al `message` español (degradación elegante).

---

## Approach técnico

- **Namespaces por área** en `es.ts`/`en.ts`: `common`, `errors`, `nav`, `auth`, `dashboard`, `orders`, `finance`, `products`, … (uno por feature). Mantiene los archivos navegables.
- **Idioma adentro de la app = locale del tenant** (lo anota el propio `i18n/index.ts`): al loguearse, setear el idioma desde `tenant.locale` (el spine ya tiene `locale`), con override manual del `LanguageSwitcher`. Así un tenant US ve inglés aunque el navegador esté en español.
- **Formato de números/fechas:** `money.ts` ya formatea por locale; revisar fechas (`toLocaleDateString`) para que respeten el idioma.
- **Parity-safe:** los strings `es` deben ser **idénticos** a los actuales → ningún usuario AR ve un cambio. La migración es aditiva.
- **Regla de oro:** UX en español para AR / inglés para US; los `code` de error siguen siendo inglés estable (no se tocan en el backend).

---

## Orden por prioridad (por lo que un usuario US toca primero)

**P0 — Camino de signup + errores** (lo primero que ve un yanqui de la landing EN):
- `components/auth/auth-layout.tsx` (panel izquierdo compartido)
- `features/identity/`: onboarding, verify-email, accept-invitation, invite-user (login ya está)
- **Frente B completo:** helper `apiErrorText` + diccionario `errors.<code>` + reemplazar los ~35 call-sites
- `LanguageSwitcher` visible en el shell (que un logueado pueda togglear)

**P1 — Shell + entrada:**
- `components/shell/` (AppShell, nav-config labels, topbar)
- `features/dashboard/` (Inicio)

**P2 — Operación core:**
- `orders`, `floor`, `kds`, `cashier`, `timeclock`, `reservations`

**P3 — Gestión + análisis:**
- `finance`, `products`, `inventory`, `expenses`, `invoices`, `analytics`, `reports`, `advisor`, `copilot`, `crm`, `integrations`, `settings`, `billing`, `platform`

*(22 áreas de feature en total; ~53 pantallas.)*

---

## Cómo ejecutar

- **Manual, por área**, en el orden P0→P3, validando build+lint+tests después de cada tanda.
- **O paralelizado con un workflow** (recomendado por la escala): fan-out de agentes, uno por área de feature, cada uno migra sus pantallas a `t()` y aporta sus keys a `es.ts`/`en.ts`; después un merge de los diccionarios. Requiere opt-in explícito del usuario ("usá un workflow").

## Validación (por tanda)

- `npm run build` (tsc + vite) + `npm run lint` + tests.
- Chequeo visual en **inglés** (toggle EN o `VITE_AUTH_BYPASS`) de las pantallas migradas.
- Verificar que en **español** no cambió nada (paridad).

## Blockers / decisiones

- **Ninguno bloqueante de negocio.** Es un proyecto de volumen (mecánico + cuidado).
- **Sub-decisión:** ¿el idioma adentro de la app lo fija el `tenant.locale` (recomendado) o queda por navegador + toggle? (Se puede empezar por navegador+toggle y sumar tenant.locale después.)
- **Backend (opcional, futuro):** si algún día se quieren `message` de error también en inglés desde el backend, es otro trabajo; con el Frente B (traducir por `code` en el front) **no hace falta** tocar el backend.

## Estimación

22 áreas · ~53 pantallas · ~1000+ strings + el diccionario de errores. Es el capítulo más grande post-landing. Conviene `/compact` + ejecución por tandas (o workflow).

---

## Arranque sugerido

**P0 primero** (auth-layout + identity + errores) — cierra el hueco visible del funnel US (landing EN → signup EN). Después P1 (shell+dashboard) y así hacia P3.
