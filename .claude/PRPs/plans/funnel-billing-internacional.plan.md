# PRP — Funnel de billing internacional (AR ↔ US) con pricing regional anti-arbitraje

> **Estado:** Hoja de ruta (NO codeado). Creado 2026-08-25.
> **Alcance:** El cobro de **nuestra** suscripción SaaS al restaurante (**Flujo A**). NO cubre los cobros que el restaurante hace a sus comensales (**Flujo B** — MercadoPago ya existe, Stripe para comensales es otro plan).
> **Relacionado:** `plan-internacionalizacion-us.md` (spine + TaxJar + i18n ya construidos), `deploy-railway.md` (landing en prod, DNS Namecheap→Railway).

---

## 1. Objetivo

Vender la suscripción de Wellnod en dos mercados con **precios distintos por poder adquisitivo (PPP)**:
- **Argentina:** precio local barato, en **ARS**, cobrado por **MercadoPago**, con factura **AFIP**.
- **Internacional (US y resto del mundo):** precio full, en **USD**, cobrado por **Stripe**.

El visitante ve **solo el precio de su región** (sin switch), y **no puede comprar el precio barato desde afuera**. La primera línea de defensa es el display geo-lockeado; el **candado real es el riel de pago + la identidad fiscal**, no la IP.

## 2. Principios (decididos con el dueño)

1. **La vidriera es blanda, el candado está en la plata.** Mostrar un precio ≠ poder pagarlo. El display geo evita que la mayoría vea el precio barato; el riel impide que el que igual lo ve (VPN) lo pague.
2. **Sin switch de moneda.** El visitante ve una sola región. El caso legítimo (argentino viajando) se resuelve en el **signup** con identidad de pago, no con un botón.
3. **Región binaria: Argentina vs Internacional.** El precio barato es específico del mercado local. Todo lo que no es AR va a USD/inglés.
4. **La región/moneda/riel de un tenant se fija en el signup y es permanente** — no depende de la IP en vivo (un negocio AR es AR aunque el dueño abra desde Miami). Reusa el spine ya construido (`tenant.country/currency/locale/tax_engine`).
5. **La IP solo decide qué se MUESTRA** (default de región en la landing anónima), nunca qué se cobra.
6. **Defensa en profundidad:** ninguna capa sola alcanza; se acumulan (edge-geo + riel + CUIT + anti-fraude + ToS).
7. **Paridad:** AR sigue funcionando igual que hoy; lo nuevo es aditivo.

## 3. Arquitectura de decisión (quién decide qué, y cuándo)

```
┌─ Anónimo (landing/pricing) ──────────────────────────────────────────┐
│  región mostrada = geo-IP en el EDGE (Cloudflare CF-IPCountry)        │
│      AR            → ES / ARS / precio local                          │
│      resto         → EN / USD / precio full                          │
│  → SOLO display. Sin switch. URLs distintas por región + hreflang.   │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓ signup
┌─ Signup (momento de la verdad) ──────────────────────────────────────┐
│  país confirmado por el usuario (pre-cargado por geo)                 │
│  → fija tenant: country, currency, locale, tax_engine, region, RIEL   │
│      AR   → ARS · MercadoPago · AFIP · CUIT obligatorio               │
│      Intl → USD · Stripe · US billing data                            │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓ checkout
┌─ Checkout (enforcement duro) ────────────────────────────────────────┐
│  plan AR   → SOLO cobrable por MercadoPago (credenciales argentinas)  │
│  plan Intl → SOLO cobrable por Stripe (USD)                           │
│  cruce de señales: IP país ≠ BIN tarjeta ≠ CUIT → block/route/review  │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓ post-pago
┌─ App (logueado) ─────────────────────────────────────────────────────┐
│  idioma  = elección usuario > tenant.locale                          │
│  moneda  = tenant.currency (fija)                                     │
│  features = gateadas por estado de suscripción                       │
│  → la IP NO se usa acá                                                │
└──────────────────────────────────────────────────────────────────────┘
```

## 4. Las capas anti-arbitraje (defensa en profundidad)

| Capa | Qué | Fuerza | Se filtra por |
|---|---|---|---|
| 0. Edge-geo display | CF-IPCountry decide qué región ve | Media (el 95% ni ve el precio barato) | VPN / URL directa |
| 1. URLs por región + hreflang | SEO-safe; bots indexan ambas | — (es correctez SEO) | — |
| 2. **Riel de pago** | Plan AR solo por MercadoPago; Intl solo por Stripe | **Alta (candado real)** | Tarjeta AR de un tercero |
| 3. Identidad fiscal | CUIT + AFIP (AR) / US data (Intl) al signup | Alta | Falsear CUIT (molesto + ilegal) |
| 4. Anti-fraude | Stripe Radar, detección VPN/proxy, cruce de señales, velocity | Media | — |
| 5. ToS | Derecho a re-tarifar/cancelar por fraude de región | Legal (red de seguridad) | — |

**Clave técnica:** Stripe casi no hace acquiring en ARS/Argentina → el plan en pesos corre por MercadoPago sí o sí, y Stripe solo USD. **Los dos rieles se separan solos** → el arbitraje se auto-bloquea sin depender de geolocalización.

## 5. Fases de implementación

### Fase 0 — Infra edge + geo (habilitador de todo)
- Poner **Cloudflare** al frente de la landing (Workers o Pages). (Encaja con migrar el DNS a Cloudflare — hoy Namecheap→Railway.)
- Leer `CF-IPCountry` / `request.cf.country` en el edge → resolver región (AR vs Internacional).
- Rutear/servir la variante correcta **antes** de que la página llegue al browser (sin flash, sin JS spoofeable).
- **Validación:** desde una IP AR ves `/` (AR); desde IP US ves la internacional; un bot puede llegar a ambas URLs.
- **Gotcha:** con hosting estático puro NO se puede diferenciar → esta fase es obligatoria y es una decisión de infra.

### Fase 1 — Landing bilingüe + pricing regional (display, sin switch)
- Landing bilingüe (ver plan de landing i18n): `EnStaticContentRepository` + `EnStaticPlanRepository`, container por idioma, prerender de ambas, `<html lang>` dinámico.
- **Pricing por región** desde el repo de planes (ARS para AR, USD para Intl). Sin toggle de moneda.
- **URLs distintas por región** (ej. `wellnod.com` = Intl/USD, `ar.wellnod.com` o `/ar` = AR/ARS) con `hreflang` es/en/x-default + canonical por idioma.
- Geo-redirect del **humano** en el edge; bots y links directos llegan a cada URL (SEO-safe).
- **Copy:** transcreación, no traducción literal (Intl vende sales tax / English copilot, no AFIP).
- **Validación:** SEO (ambas URLs indexables, hreflang correcto), un visitante US no ve ARS por default.

### Fase 2 — Modelo de planes + billing backend (spine de suscripción)
- **Dominio:** entidades `Plan` (tier, features, precio por región/moneda, ciclo) y `Subscription` (tenant, plan, estado, período, riel). Python puro.
- **Puertos:** `BillingGateway` (crear/cancelar suscripción, portal) con dos adapters: **Stripe Billing** (USD) y **MercadoPago Preapproval** (ARS — API de suscripciones, distinta de los pagos one-shot que ya usás).
- **Tablas:** `plans` (catálogo) + `subscriptions` (RLS) + estado por tenant. El tenant ya tiene `country/currency`; se agrega `region` + `subscription`.
- **Gating:** un `SubscriptionPolicy` que decide qué features están habilitadas por plan/estado (feature flags por tier Básico/Pro).
- **Validación:** crear una suscripción fake por cada riel; el gating prende/apaga features.

### Fase 3 — Signup + checkout con riel por región (el corazón anti-arbitraje)
- **Signup:** país confirmado por el usuario (pre-cargado por geo) → fija `region/currency/locale/tax_engine/riel`.
- **Región AR:** checkout **MercadoPago** (ARS) + **CUIT obligatorio** + datos AFIP.
- **Región Intl:** checkout **Stripe** (USD) + datos de facturación US.
- **Enforcement:** el use case rechaza pagar el plan AR por un riel que no sea MercadoPago, y viceversa. Cruce de señales (IP país, BIN de la tarjeta, CUIT) → `block` / `route a USD` / `review`.
- **Webhooks:** pago exitoso/fallido/cancelación → actualizan el estado de la suscripción → gating.
- **Validación:** e2e por región; un intento de pagar el plan AR con tarjeta US se bloquea/rutea.

### Fase 4 — Anti-fraude + operación (producción)
- **Stripe Radar** + reglas (BIN country, velocity).
- **Detección de VPN/proxy** (MaxMind / IPQualityScore) → flag si viene por VPN pidiendo precio AR.
- **Dunning:** reintentos de cobro fallido + grace period antes de degradar el plan.
- **ToS** con cláusula anti-abuso de región (re-tarifar/cancelar).
- **Panel interno:** ver suscripciones, estados, flags de mismatch.

### Fase 5 — Facturación / compliance por región
- **AR:** factura AFIP de la suscripción (¿reusa el dominio `invoice` existente o es un flujo B2B aparte?). Tipo de comprobante a definir.
- **Intl:** invoice/recibo US. **¿Cobramos sales tax sobre el SaaS?** Depende del nexus (SaaS es taxable en varios estados US). Reusa TaxJar si aplica.
- **Entidad legal:** ¿una o dos? (Una entidad US para USD/Stripe + la AR para ARS/AFIP.)

## 6. Decisiones de negocio pendientes (bloquean el diseño final)

1. **Precios concretos** (ARS y USD) por tier.
2. **Resto del mundo = USD/inglés** (confirmar; simplifica el catálogo). Recomendado.
3. **Tiers** (Básico/Pro/…) y qué features gatea cada uno.
4. **¿Trial? ¿Freemium?** Afecta el flujo de signup.
5. **¿Sales tax sobre el SaaS US?** (nexus por estado).
6. **Entidad(es) legal(es)** para USD/Stripe y ARS/AFIP.
7. **Comprobante AR** (tipo de factura AFIP para la suscripción).
8. **Dominio de la región AR** (subdominio `ar.` vs path `/ar`) — afecta SEO y edge routing.
9. **¿Argentino que quiere pagar en USD?** (política para el caso borde legítimo).

## 7. Riesgos / gotchas

- **SEO:** el geo-redirect por IP mal hecho hace que Google indexe una sola versión. Hay que hacerlo bien (URLs crawleables + hreflang + redirect solo del humano). Trampa #1.
- **Edge compute obligatorio:** no alcanza con hosting estático (Fase 0).
- **MercadoPago Preapproval** (suscripciones recurrentes) es una API distinta de los pagos que ya usás — hay que integrarla de cero.
- **Fuga por VPN:** existe; la corta el pago, no el display. Se acepta.
- **Complejidad de estados de suscripción + webhooks + dunning + gating:** es el grueso del backend.
- **Complejidad legal/fiscal:** dos jurisdicciones, quizá dos entidades, dos flujos de factura. Lo más pesado y NO es de código.
- **Stripe no hace ARS acquiring** → por eso ARS va por MercadoPago (esto es una feature, no un bug: separa los rieles).

## 8. Fuera de alcance (de ESTE plan)

- **Flujo B** (cobros del tenant a sus comensales): MercadoPago ya existe; Stripe para comensales US es otro plan.
- Más de dos regiones/monedas (se diseña binario AR vs Intl; extensible después con el mismo spine).
- Migración del sistema a multi-moneda por transacción (no aplica: un tenant = una moneda).

## 9. Camino crítico

**Fase 0 (edge-geo) → Fase 1 (landing+pricing) → Fase 2 (billing backend) → Fase 3 (signup+checkout).** Las Fases 4 y 5 endurecen y dan compliance, se pueden solapar. **Empezar por Fase 0** (sin edge-geo no hay diferenciación de display posible) y por destrabar las **decisiones de negocio** de la sección 6 (precios, tiers, entidad legal), que son el verdadero bloqueante.
