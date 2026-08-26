# PRP — i18n de la app (`app.wellnod.com`) — español ↔ inglés

> **Estado:** ✅ **COMPLETA** (P0–P3). Creado 2026-08-26. **P0 (`a873fb3`) + P1 (`35c1822`) + P2 (`d98a030`) + P3-A (`e4e43bd`) + P3-B (`72c6ac6`) en `main`.** Las 54 pantallas de `app.wellnod.com` son bilingües ES/EN. Único pendiente: la **pasada de formato** (`es-AR` de fechas/horas/números → locale activo).
> **Objetivo:** que un restaurante de EE.UU. use **toda la app en inglés** (no solo el login). Hoy la landing EN manda al usuario a una app en español → rompe el funnel US.
> **Relacionado:** `landing-internacional.plan.md` (la landing ya es bilingüe + geo), `plan-funnel-billing.md`.

## Progreso

- **Fundación ✅:** locales troceados en **namespaces por feature** (`locales/{es,en}/*.ts` + barrels; adiós a los 2 archivos planos). Helper **`apiErrorText(error, t, fallback)`** (`src/api/translate-error.ts`) traduce por `code`. Diccionario **`errors` completo en inglés** (79 codes); **es vacío a propósito** → fallback al `message` del backend = paridad AR exacta. Cada feature futura solo agrega su namespace + swapea sus call-sites de error.
- **P0 ✅** (`a873fb3`): `auth-layout` (panel de marca) + 4 pantallas de identity (onboarding / verify-email / accept-invitation / invite-user) a `t()` + `apiErrorText`; schemas zod movidos adentro con `useMemo([t])`. `<LanguageSwitcher/>` visible en el menú de usuario. Namespaces `auth`, `identity`. Login ya estaba.
- **P1 ✅** (`35c1822`): **shell** (namespace `shell`: nav-config con labels→claves resueltas en `app-shell`, grupos, menú, aria, reloj) + **dashboard** (namespace `dashboard`: Home completo; helpers puros `daily-verdict`/`home-alerts` refactorizados a **keys+params** con plurales nativos i18next, tests actualizados).
- **P2 ✅** (`d98a030`): 6 áreas de operación en un workflow de **6 agentes** (uno por área, archivos + libs disjuntos). Namespaces `orders`, `floor`, `kds`, `cashier`, `timeclock`, `reservations`. Mapas de labels de estado movidos del código al diccionario (`floor.state.*`, `reservations.statusLabels/turnLabels.*`, `cashier.methodLabels/movement*.*`, `timeclock.shiftSource.*`) y resueltos con `t()`; enums intactos. Labels del recibo/comanda impresos inyectados vía `t()` (+ bug de `CobroSection` corregido). `floorView` intacto (lo usa el dashboard). Se quitó el test de constantes de reservations (212→**211**, justificado).
- **Ejecución:** por **workflow** (2–6 agentes/tanda sobre archivos disjuntos; fundación inline = crear namespaces stub + registrarlos en barrels = seam). Validación por tanda: build + lint + tests + grep anti-strings ES + paridad char-por-char.
- **Follow-up conocido (pasada de formato):** `topbar-clock.tsx` y `lib/timeclock.ts` (y otros) usan `toLocaleTimeString/DateString("es-AR")` → un usuario EN ve hora/fecha en formato AR. Derivar el locale del idioma activo de i18next = pasada de formato (fechas/números/hora), pendiente.

- **P3 ✅** (gestión, 14 áreas) en **dos sub-tandas** de 7 agentes: **P3-A** (`e4e43bd`: products, finance, inventory, invoices, expenses, analytics, reports) + **P3-B** (`72c6ac6`: advisor, copilot, crm, integrations, settings, billing, platform). Labels de categoría/estado/segmento/bucket movidos del código al diccionario y resueltos con `t()`; enums intactos. Frases con negrita/varias variables troceadas en claves-fragmento por idioma (no hay `<Trans>` en el repo). Respuestas del backend (copiloto, diagnóstico, planes) NO se traducen.

**Sweep final:** en TODA la app queda **1 sola** línea con ES de UI — `products/pricing.ts` `WEEKDAY_LABELS` — intencional (la testea `pricing.test.ts`; la UI ya usa `products.weekdays`).

## Pendientes (no bloqueantes)

1. **Pasada de formato:** varios usan `toLocaleTimeString/DateString/String("es-AR")` e `Intl` con locale fijo (`topbar-clock`, `lib/timeclock`, `product-ficha`, `pricing-inflation-card`, etc.) → un usuario EN ve hora/fecha/número en formato AR. Fix = derivar el locale del idioma activo de i18next en un helper de formato central.
2. **Constantes de lib vivas solo para sus tests** (dead-for-UI, inofensivas): `pricing.WEEKDAY_LABELS`, `lib/advisor.BUCKET_LABELS`, `lib/timeclock.SHIFT_SOURCE_LABELS` (movido), `lib/floor-session` labels. Si se limpian, actualizar sus tests.
3. **Doc-types AFIP/ARCA** (`lib/invoice-labels`) quedan en ES a propósito (concepto fiscal AR; un restaurante US usa recibos de sales tax).
4. **Idioma adentro de la app:** hoy manda navegador + toggle persistido. Falta (opcional) fijarlo por `tenant.locale` al loguearse.

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
