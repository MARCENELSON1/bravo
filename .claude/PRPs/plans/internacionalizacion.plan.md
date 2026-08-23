# PRP — Internacionalización de Wellnod (mercado US) + Cadenas multi-local

> **Estado:** hoja de ruta (no implementado). Spec-driven, para ejecutar con `/prp-implement`.
> **Fecha:** 2026-08-23.
> **Alcance:** llevar Wellnod a poder venderse a locales de EE.UU. (multi-tenant, multi-moneda, multi-régimen fiscal) **sin romper la paridad** de los tenants argentinos actuales, y habilitar **cadenas multi-local** bajo una marca.

---

## 0. Principios rectores (no negociables)

1. **Paridad total.** Todo cambio es aditivo: columnas nullable con **default AR**, flags opt-in OFF, resolvers que caen a AR si no hay config. Un tenant argentino existente debe verse **idéntico a hoy** tras cada fase.
2. **Ports & Adapters.** Todo lo país-específico (impuesto, facturación, pagos, motor de tasa) vive **detrás de un puerto** con su adapter en `infrastructure`. La elección se hace **por tenant en runtime** vía un **resolver**, no al arrancar la app.
3. **El spine primero.** El tenant gana campos de identidad regional (`country`, `tax_regime`, `currency`, `locale`, `timezone`, `tax_engine`). **Todo lo demás lee de ahí.** Sin spine, nada sabe "quién es AR y quién es US".
4. **Clean Architecture intacta.** `domain` puro; los casos de uso dependen de puertos; la DI se cablea en `container.py`; multi-tenant filtra por `tenant_id` + RLS.

---

## 1. Aclaración base: son DOS flujos de plata distintos

No mezclar — cada uno usa su propio motor:

| Flujo | Qué es | Motor |
|---|---|---|
| **A. El restaurante te paga a vos** | Suscripción SaaS (*pricing / paga* del funnel) | **Stripe Billing** (USD) / MercadoPago o actual (ARS) |
| **B. Los clientes le pagan al restaurante** | Cobro dentro de la app (*consume del sistema*) | **Stripe** (tarjeta US) / efectivo — y **TaxJar** calcula el sales tax |

La cuenta de Stripe del usuario sirve para los dos, pero son **integraciones separadas**.

---

## 2. Arquitectura del spine + resolvers

Un tenant gana identidad regional; los casos de uso piden al **resolver** el adapter correcto según esa identidad.

```python
# domain/tax/regime.py
class TaxRegime(Enum):
    AR_AFIP = "AR_AFIP"
    US_SALES_TAX = "US_SALES_TAX"

class TaxEngine(Enum):
    NONE = "NONE"        # AR: el impuesto sale del régimen, no de un motor externo
    TAXJAR = "TAXJAR"    # US SMB
    AVALARA = "AVALARA"  # US enterprise (diferido)

# Resolver de facturación (AFIP vs recibo US) — decide por régimen
class TaxGatewayResolver(ABC):
    @abstractmethod
    def for_regime(self, regime: TaxRegime) -> InvoicingGateway: ...

# Resolver de motor de tasa (TaxJar vs Avalara) — decide por tenant
class TaxEngineResolver(ABC):
    @abstractmethod
    def for_tenant(self, tenant) -> TaxCalculator: ...
```

`IssueInvoice` (y el cobro) leen `tenant.tax_regime` / `tenant.tax_engine` → el resolver devuelve el adapter → operan. **El caso de uso queda agnóstico del país.** El container cablea TODOS los adapters + los resolvers (no "uno u otro").

---

## 3. Modelo de datos: local = tenant, marca = organization

- **Local = `tenant`** (unidad de aislamiento). Caja, stock, mesas/salón, órdenes, fichaje, **régimen fiscal + moneda + locale**, pagos → todo por local. Lo obliga la realidad: caja/stock/mesas son por local y **el impuesto es por local** (punto de venta AFIP en AR; jurisdicción de sales tax por dirección en US).
- **Marca = `organization`** (capa encima). Menú/recetas maestras, identidad, roles de cadena, **reporting consolidado**, benchmarking entre locales.
- Un resto solo es un tenant con `organization_id = NULL` → **paridad**.
- **Sinergia clave:** como el régimen/moneda/locale viven en el local, una **cadena multi-país** (locales AR + US bajo la misma marca) sale casi gratis; la org solo agrega y convierte a una moneda de reporte.

---

# PARTE A — El viaje del usuario US (end-to-end)

| Paso | Qué ve el usuario US | Qué requiere por debajo |
|---|---|---|
| **1. Landing** (`wellnod.com`) | Landing en inglés, mensajes/moneda US | Detección de locale (país / `Accept-Language`) + ruteo → versión EN |
| **2. Pricing** | Planes en USD | Precios por mercado (USD/ARS) + definir si cobrás sales tax sobre el SaaS |
| **3. Registro / Onboarding** | Elige país = US | Setea el **spine**: `country`, `tax_regime=US_SALES_TAX`, `currency=USD`, `locale=en-US`, `timezone`, `tax_engine=TAXJAR` |
| **4. Paga la suscripción** | Checkout en USD | **Stripe Billing** (suscripción recurrente del SaaS) |
| **5. Usa el sistema** | App en inglés, plata en USD, ticket con tax arriba, cobra por Stripe/efectivo, reportes en su huso | i18n + `TaxMode=ADDED` + TaxJar + US receipt gateway (sin CAE) + Stripe cobro + rollups TZ-aware + unidades imperiales |

---

# PARTE B — El plan de construcción (orden por dependencias)

El usuario vive el funnel 1→5, pero se construye desde el spine hacia afuera.

## FASE 0 — El spine (tenant locale/regime-aware) · *base de todo*

**Objetivo:** que cada tenant tenga identidad regional y que los resolvers puedan leerla.

**Cambios de datos** (migración ≈0039, aplicar a dev; prod vía preDeploy):
- `tenants.country` (existe, default `"AR"`).
- `tenants.tax_regime` (default `AR_AFIP`).
- `tenants.locale` (default `es-AR`).
- `tenants.timezone` (default `America/Argentina/Buenos_Aires`).
- `tenants.tax_engine` (default `NONE`).
- `currency` ya existe.
- Todo **nullable/default AR → paridad**.

**Dominio / aplicación:**
- VOs `TaxRegime`, `TaxEngine`, `Locale`, `Timezone`.
- `TaxGatewayResolver` + `TaxEngineResolver` (interfaces en `domain`, adapters registran AR por defecto).
- `OnboardTenant` acepta `country` → deriva defaults del país (US → regime/currency/locale/engine).

**Gates:** back tests + ruff; test de **paridad** (tenant sin país nuevo ⇒ comportamiento idéntico). Migración aplicada a dev.

---

## FASE 1 — i18n de la app · *para que un tenant US vea inglés*

- Framework **`react-i18next`** + extracción de strings + catálogo **`en-US`** (el grueso, mecánico, bajo riesgo).
- Formateo por locale: **`Intl.NumberFormat`** para plata/fechas (hoy asume AR: coma decimal, `$`). Revisar `formatMoney`, CSV del contador (usa coma), y todo hardcode de `$`/`ARS`.
- **Emails** por locale (templates hoy en español).
- **Prompts del Asesor/Copiloto** en inglés + narración por locale.
- Semana empieza **domingo**, hora **12h**.

**Gates:** front build + lint + vitest; snapshot visual EN/ES. Paralelizable con Fase 2.

---

## FASE 2 — Fiscal & operaciones US · *el corazón*

- **`TaxMode`** (INCLUSIVE AR = IVA incluido / **ADDED US** = tax arriba) → toca el cobro y el desglose del ticket. En US el precio de carta es **neto** y el tax se suma; el margen es más simple (no hay que netear).
- Puerto **`TaxCalculator`** + **`TaxJarAdapter`** + `TaxEngineResolver` (diseñado para 2 motores, se implementa 1). Llamado al **armar el total** (`/v2/taxes`) y al cerrar (`/v2/transactions/orders` → AutoFile). **Agnóstico del medio de pago** (cubre efectivo).
- **`USReceiptGateway`** (numera recibo, sin CAE/WSAA/comprobante) detrás del puerto de facturación existente. Campos AR (CAE, tipo A/B, CUIT, condición IVA) → nulos.
- **`StripeGateway`** (cobro con tarjeta del restaurante) detrás del `PaymentGateway` existente. Puerto separado del de impuestos.
- **Rollups diarios TZ-aware** (hoy trunca en UTC → día corrido en US): cortes de día por `tenant.timezone`.
- **Unidades imperiales** (lb/oz/gal/floz) en el enum de unidades + conversiones (reusar `UnitOfMeasure.parse`).

**Gates:** back tests + ruff; e2e de cobro US (tax added, recibo sin CAE); e2e de paridad AR (AFIP intacto).

---

## FASE 3 — Funnel de adquisición · *landing → pricing → billing*

- **Landing en inglés** + ruteo por locale (`wellnod.com`).
- **Pricing en USD** + planes por mercado.
- **Stripe Billing** para la suscripción SaaS (distinto del cobro del restaurante).
- Onboarding conectado al spine (Fase 0).

**Gates:** front build; flujo signup→checkout→tenant creado con spine US, verificado en staging.

---

## FASE 4 — Enterprise (Avalara) · *diferida, cuando aparezca la cadena grande*

- **`AvalaraAdapter`** en el mismo `TaxEngineResolver` → un adapter nuevo, **no reescritura**.
- Define el puerto `TaxCalculator` como **mínimo común denominador** (ubicación + ítems con tax code + montos → impuesto); los extras de Avalara (certificados de exención, returns) van por flujos aparte, aditivos.
- `tenant.tax_engine` explícito, con default derivado del plan (Enterprise → Avalara disponible), override permitido.

---

# TRACK PARALELO — Cadenas multi-local (Organization)

Independiente del país (usa el mismo spine). El valor que **más vende** a una cadena es el reporting consolidado/benchmarking (reusa el motor del Asesor).

## Fase C0 — Fundación (no rompe nada)
- Tabla `organizations` + `tenants.organization_id` **nullable** (resto solo = tenant sin org → paridad).
- Membresía de usuario a nivel org.

## Fase C1 — Reporting consolidado
- Read-models cross-tenant scopeados por `organization_id` (rollup de facturación, comparativa entre locales, **benchmarking** de food cost/margen). Read-only, aditivo.
- Multi-moneda: convertir a una **moneda de reporte** de la marca (habilita cadenas multi-país).

## Fase C2 — Catálogo maestro (la fase invasiva)
- Productos/recetas **de marca** heredados por local, con **override** local de precio + disponibilidad.
- Toca el modelo de propiedad del catálogo → al final, con cuidado.

## Fase C3 — Cross-local
- Transferencia de stock entre locales, compras consolidadas a proveedores.

## Riesgos del track cadenas (diseñar con cuidado)
1. **RLS/acceso cross-local:** hoy la policy aísla por `tenant_id`. Para que el dueño de cadena lea varios locales, extender el acceso a "set de tenants autorizados por su org" (`tenant_id IN (...)`). **Parte de seguridad más delicada** — test de aislamiento fuerte.
2. **Switch de local en la sesión:** el JWT/sesión necesita "local actual" + "locales autorizados" (estilo workspaces).

---

# Decisiones de negocio (bloqueantes, no técnicas)

1. **Pricing en USD:** ¿qué planes, a qué precio?
2. **¿Cobrás sales tax sobre tu propia suscripción SaaS?** (la taxabilidad del SaaS varía por estado — probablemente sí en varios).
3. **Legal/entidad** para cobrar USD por Stripe (¿entidad US o el modelo cross-border de Stripe alcanza?).
4. **¿English-only o bilingüe al lanzar?** (define cuánto de Fase 1 se hace ya).
5. **Motor fiscal:** TaxJar para arrancar (SMB + AutoFile); Avalara solo cuando entre enterprise.

---

# Orden recomendado / camino crítico

- **Crítico:** Fase 0 → Fase 2 (spine + fiscal/operaciones).
- **Paralelo, bajo riesgo:** Fase 1 (i18n).
- **Al final:** Fase 3 (funnel, depende del spine).
- **MVP US real:** Fase 0 + Fase 2 + un mínimo de Fase 1 y Fase 3.
- **Cadenas:** arrancar por C0 (fundación nullable) + C1 (consolidado) cuando haya demanda; C2/C3 después.

**Empezar por la Fase 0:** chica, no rompe nada (todo default AR), desbloquea todo lo demás.

---

# Validación global (definition of done por fase)

- Back: `pytest` verde + `ruff` limpio + migración aplicada a dev.
- Front: `npm run build` + `lint` + `vitest` verde.
- **Paridad:** un tenant AR existente se comporta idéntico a hoy (test explícito por fase).
- Merge `--no-ff` por consola, push a `main` (deploya a prod), reporte en `reports/`.

---

# Notas de seguridad / operación (pendientes del proyecto)

- Rotar: password Postgres prod + `ANTHROPIC_API_KEY` (compartidas en chat).
- Limpiar data de prueba en prod (tenant "aaaaa").
- No commitear nunca: `.mcp.json`, `LOG-DIGITAL-N212WT.md`, `me.py`, `auth.py`, `dist-electron/`, `proyecto Well Nod 2026/`, `Documents/`, `infra/`.
