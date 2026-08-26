# PRP — Landing internacional (regional, geo-lockeada, SSR-safe) — PASO A PASO PRODUCTIVO

> **Estado:** Hoja de ruta (NO codeado). Creado 2026-08-25.
> **Objetivo:** que la landing muestre **inglés + USD** a un visitante de EE.UU. y **español + ARS** a uno de Argentina, **sin switch**, y **sin romper SEO**.
> **Relacionado:** `funnel-billing-internacional.plan.md` (esto es su **Capa 0/1** — el display; el candado de la Capa 2 = el riel ya está construido), `plan-funnel-billing.md`, `deploy-railway.md` (landing en Railway service `landing`, DNS Namecheap→Railway).

---

## Contexto de la landing (cómo está hoy)

App **separada** (`~/Desktop/BRAVO/landing`): Vite + React 19 con **SSR/prerender** (Clean Arch domain/application/infrastructure/presentation). `createContainer()` newa `StaticPlanRepository` + `StaticContentRepository`. `entry-server.tsx render()` renderiza con el container; `scripts/prerender.mjs` inyecta el HTML en **una** `dist/index.html`; `main.tsx` hidrata. `index.html` = `<html lang="es">` + title/meta/OG/canonical en español. Copy: parte en los repos (features/pasos/FAQs/planes), parte **hardcodeada en ~15 componentes de sección**.

## Principio rector

**El candado es el riel de pago (ya hecho), no la IP.** Esta landing es el **display**: la IP/geo solo decide QUÉ ve el visitante; si igual ve el precio barato, no puede pagarlo (plan AR solo por MercadoPago). Por eso el display puede ser "blando" y priorizamos **SEO + UX** sobre bloqueo perfecto.

---

## FASE A — Parametrizar la landing por región (código, sin deploy)

**A1. Definir región/locale.**
- `Region = 'AR' | 'INTL'`, `Locale = 'es-AR' | 'en-US'`. Mapear región→locale→moneda (AR→es-AR/ARS, INTL→en-US/USD).

**A2. Container por región.**
- `createContainer(region: Region)` → elige los repos de esa región. Es el seam natural (el container ya es "el único que conoce las implementaciones concretas"). Cambia solo esas líneas.

**A3. Repos EN + planes por región.**
- `EnStaticContentRepository` (transcreación, ver Fase E) + `EnStaticPlanRepository` (o un `PlanRepository` que reciba la región).
- **Pricing = fuente de verdad del billing:** los precios de la landing deben salir de los planes reales (`GET /billing/plans?region=`), NO hardcodeados aparte. Opción productiva: fetch **en build** (prerender) para incrustar precios frescos + revalidar en cada deploy; o fetch client-side con el prerender como fallback. Decisión: build-time fetch (SSR-friendly, se re-deploya al cambiar precios).

**A4. Strings del "chrome" por locale.**
- Extraer los strings hardcodeados de los ~15 componentes de sección a un diccionario por locale (un `strings[locale]` simple o `react-i18next` como en la app). Los componentes leen del locale del container/context.

## FASE B — Prerender de las dos versiones + SEO

**B1. `render(region)` en `entry-server.tsx`** → renderiza con `createContainer(region)`.

**B2. `prerender.mjs` genera DOS HTML:**
- `dist/index.html` → **es-AR**: `<html lang="es">`, title/meta/OG en español, `canonical https://wellnod.com/`.
- `dist/en/index.html` → **en-US**: `<html lang="en">`, title/meta/OG en inglés, `canonical https://wellnod.com/en/`.

**B3. `hreflang` + `x-default` en AMBAS** (dentro del `<head>`):
```html
<link rel="alternate" hreflang="es-AR" href="https://wellnod.com/" />
<link rel="alternate" hreflang="en-US" href="https://wellnod.com/en/" />
<link rel="alternate" hreflang="x-default" href="https://wellnod.com/" />
```

**B4. Hidratación por locale.** `main.tsx` lee `document.documentElement.lang` → `createContainer(region)` que **coincide** con el HTML servido → sin mismatch de hidratación.

**B5. Sitemap + robots** con ambas URLs.

## FASE C — Edge-geo con Cloudflare (infra)

**C1. Migrar el DNS de `wellnod.com` a Cloudflare** (hoy Namecheap→Railway). Cloudflare como proxy (naranja) delante del service `landing`. *(Ya lo teníamos anotado como habilitador.)*

**C2. Cloudflare Worker / Pages Function** (el ruteo geo):
- Lee `request.cf.country` (país por IP, gratis en CF).
- **Servir por path:** `/` → `dist/index.html` (AR/es); `/en/*` → `dist/en/index.html` (INTL/en). Ambas URLs accesibles directo (bots + links).
- **Redirect del HUMANO (SEO-safe):** en `/`, si `country != 'AR'` **y** no hay cookie `wellnod_region` → `302` a `/en/` + set cookie. Si hay cookie o es AR → sirve `/`. **Nunca** redirigir por User-Agent; los bots llegan a cada URL directo y `hreflang` los guía (esto evita la trampa SEO #1: Googlebot crawlea desde US → si redirigís por IP a ciegas, solo indexa `/en`).
- Selector opcional de región en el footer que setea la cookie (para el caso legítimo: argentino que quiere ver en inglés, o al revés).

**C3. Cache** de las dos HTML en el edge (Cache Rules); purgar en cada deploy.

## FASE D — Deploy + verificación

**D1.** Build de la landing → `dist/index.html` + `dist/en/index.html` (+ assets, sitemap, robots).
**D2.** Deploy (Railway sirve `dist/`; Cloudflare Worker rutea + geo).
**D3. Verificar:**
- IP AR → `wellnod.com` = **ES/ARS**.
- IP US (VPN) sin cookie → `302` a `/en/` = **EN/USD**.
- `wellnod.com/en/` directo → EN/USD (simula bot/link).
- `curl` con `CF-IPCountry` distintos → la variante correcta.
- **Google Search Console:** hreflang sin errores, ambas indexadas.
- **Lighthouse SEO** OK en las dos; sin flash de idioma (prerender correcto).

## FASE E — Copy en inglés (transcreación) — DECISIÓN DE PRODUCTO

**NO es traducción literal.** La landing AR vende **AFIP** + "copiloto en español"; la US vende:
- **Sales tax automático** (no AFIP/CAE).
- **English copilot** (consultas en inglés).
- Mensaje US: comandas + cobros (Stripe) + sales tax + fichaje + IA, en inglés.
- Ajustar features/pasos/FAQs/planes + title/meta/OG.

→ **Claude drafts el copy EN; el dueño lo revisa y aprueba** (es la vidriera pública). Los precios USD deben matchear los planes del billing.

## Decisiones de negocio pendientes (del usuario)

1. **Copy EN** (transcreación) — Claude draftea, vos aprobás.
2. **Precios USD** de la landing (= planes del billing INTL).
3. **Resto del mundo** = INTL/USD/inglés (confirmar; recomendado).
4. **`/en` (path) vs `en.wellnod.com` (subdominio)** — recomiendo **path `/en`** (hreflang más simple, un solo cert).
5. **Migrar DNS a Cloudflare** (acción de infra tuya).

## Riesgos / gotchas

- **SEO (trampa #1):** geo-redirect mal hecho → Google indexa una sola versión. Mitigación: URLs crawleables directas + `hreflang` + redirect **solo del humano** con cookie, nunca por User-Agent ni IP a ciegas.
- **Cloudflare** = nuevo eslabón de infra (necesita tu DNS).
- **Sincronía de copy** ES/EN (mantener ambos).
- **Pricing:** la landing debe leer los precios reales del billing (una sola fuente de verdad), no una copia hardcodeada que se desactualiza.
- **Hidratación:** el locale del client DEBE coincidir con el HTML servido (leer de `<html lang>`), o React tira el markup.

## Orden de ejecución sugerido

**E (copy, se puede adelantar ya) → A (container/repos/strings) → B (prerender+hreflang+hidratación) → C (Cloudflare) → D (verificación).**
Camino crítico: A→B→C. La Fase C (Cloudflare) se puede diferir usando **detección por navegador** en una v0 (sin edge-geo), pero la versión **productiva/SEO-correcta** es con Cloudflare edge-geo (esta).
