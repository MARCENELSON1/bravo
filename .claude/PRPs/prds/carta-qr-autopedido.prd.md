# PRD — Carta QR + Autopedido + Pago desde la mesa

> **Estado:** Borrador (NO codeado). Creado 2026-08-27.
> **Autor:** propuesta del dueño; PRD anclado al código actual de Wellnod.
> **Relacionado:** motor de `Order`/`OrderItem`, `Table`/floor, KDS, `Payment`/MercadoPago, `Invoice`/ARCA, `Product`, CRM. Convención PRP: `.claude/PRPs/prds/`.

---

## 1. Problema / oportunidad

Hoy el cliente que llega al restaurante depende 100% del mozo para ver la carta, pedir y pagar. Eso genera: esperas, carga operativa del mozo, menos rotación de mesas, y **cero dato del cliente** hasta que paga (si es que se captura).

**La oportunidad:** el cliente escanea un **QR en la mesa** → ve la **carta digital completa** → arma su pedido → (opcional) **paga desde el celular**. Todo aterriza en el pipeline que Wellnod **ya tiene** (KDS, caja, ARCA, finanzas, CRM, copiloto).

**Por qué Wellnod y no un QR-menú suelto:** el 90% del trabajo pesado ya está construido. Un QR-menú de la competencia es un PDF lindo y aislado; el nuestro está **integrado a la operación real** (cocina en vivo, cobro, factura fiscal, historial del cliente, IA). Ese es el moat.

## 2. Usuarios y flujo

- **Comensal (nuevo actor, sin login):** escanea el QR de su mesa, navega la carta, arma el carrito, pide y/o paga.
- **Mozo / cajero / cocina (actores existentes):** reciben el pedido en el flujo de siempre (KDS/floor/caja), con un **gate de confirmación opcional**.
- **Dueño/encargado:** configura la carta, activa/desactiva el autopedido y el pago, imprime/gestiona los QR por mesa.

Flujo objetivo (Fase 3 completa):
`QR mesa → sesión pública de mesa → carta → carrito → crear Order → (gate mozo opcional) → KDS → pagar (MercadoPago) → factura ARCA → CRM/finanzas`.

## 3. Alcance por fases (recomendado: no todo de golpe)

La adopción cae a medida que el paso es más ambicioso (sobre todo en AR), así que cada fase deja valor solo:

### Fase 1 — Carta digital (solo ver) 🟢 bajo riesgo, alto valor
- QR por mesa → página pública, branded, **bilingüe (reusa el i18n)**, con la carta del catálogo actual (categorías, precios).
- Opcional: botones **"Llamar al mozo"** y **"Pedir la cuenta"** (notifican al floor/caja sin crear orden).
- Reemplaza el PDF/imagen de carta. **Deja armado el plumbing de QR + sesión de mesa.**

### Fase 2 — Autopedido (carrito → comanda)
- El carrito crea una `Order` que cae en **KDS/floor** como cualquier comanda.
- **Gate configurable por tenant:** los ítems entran como "pendientes de confirmación" y el mozo los marcha (o auto-marcha si el local lo prefiere).
- Requiere enriquecer el producto (fotos, descripción, **modificadores**, disponibilidad).

### Fase 3 — Pago desde la mesa
- El comensal paga desde el celu con **MercadoPago** (mismo `charge()` que ya usa el mozo), con **propina**, **factura ARCA** y **dividir la cuenta**.
- Cierra el loop transaccional completo.

## 4. Qué REUSA del código actual (el 80% ya está)

| Necesidad | Ya existe en | Nota |
|---|---|---|
| Comanda + ítems + ciclo | `domain/order` (`Order`/`OrderItem`, estados SENT/PREPARING/READY) | El pedido del cliente ES una `Order` |
| Mesa + estados del salón | `domain/table` + floor (FREE/OPEN/TO_SERVE/…) | Atar la sesión a `table_id` |
| Cocina en vivo | KDS (`lib/kds`, `station-board`, SSE) | El pedido aparece solo |
| Pago + link/QR MercadoPago | `domain/payment` (`PaymentGateway.charge()`, webhook `fetch_status`/`verify_signature`, OAuth Connect por tenant) | **El pago del cliente = el mismo `charge()`** que hoy dispara el mozo ("Abrir checkout / QR") |
| Factura fiscal | `domain/invoice` + ARCA (CAE) | Facturar el pago del cliente |
| Propina | tip flow (migr. 0014) | Reusar |
| Cliente / historial | CRM (`customers`, segments, actions) | Atar la orden a un cliente (opcional, para loyalty) |
| Finanzas / IA | Finance + Asesor/Copiloto | El dato entra solo → mejora el copiloto |
| Endpoint público sin auth | `presentation/api/v1/public.py`, `leads.py`, `webhooks.py` | Molde para las rutas del comensal |
| **QR + token challenge** | **timeclock presence** (QR + código tipeable + token firmado) | **Molde ideal para la sesión de mesa** |
| Multi-tenant + RLS | transversal | La sesión de mesa filtra por `tenant_id` |

## 5. Qué hay que AGREGAR (los gaps reales)

1. **Enriquecer el producto** (`domain/product/entities.py` hoy tiene solo `name, price, category, station, active`):
   - `image_url` / foto, `description`.
   - **Modificadores / variantes** (ej. "sin cebolla", "punto de cocción", tamaños, extras con precio). Es lo más grande — entidad/tabla nueva `ProductModifier` + selección en el `OrderItem`.
   - **Disponibilidad del día ("86'd")**: distinto de `active` (baja permanente). Un flag/stock de "hoy no hay".
2. **Sesión pública de mesa** (nuevo): token firmado por `(tenant_id, table_id[, expiración])`, emitido al generar el QR. Rutas `/public/table/{token}/...` (carta, carrito, order, pay). Anti-abuso: expiración, rate-limit, opcional "PIN de mesa" que rota.
3. **Carta pública de cara al comensal** (nuevo front): superficie liviana (ruta nueva en la app o mini-app aparte), sin auth, mobile-first, bilingüe. **Reusa el diseño/tema** ya existente.
4. **Casos de uso del comensal** (nuevos, públicos): `GetPublicMenu`, `SubmitCustomerOrder` (con gate), `PayCustomerOrder` (envuelve `charge()`), `RequestWaiter`/`RequestBill`.
5. **Gate de confirmación** (config por tenant, como `require_open_cash_session`): estado "pendiente de confirmación" del `OrderItem` o de la `Order`.
6. **Config + gestión de QR**: pantalla para prender/apagar autopedido y pago, e imprimir/descargar los QR por mesa.
7. **Split / propina en pago del cliente**: UI + lógica de dividir cuenta (el motor de pago parcial ya existe — order-page tiene "Cobrar un monto", "Dividir por ítem").

## 6. Modelo de datos (nuevo, incremental)

- `product`: **+** `image_url`, `description`, `available_today` (o tabla de disponibilidad por día).
- `product_modifier` / `modifier_option` (nuevas): grupos de modificadores por producto (mín/máx, precio por opción).
- `order_item`: **+** referencia a las opciones de modificador elegidas + `source` (`WAITER` | `CUSTOMER_QR`) para métricas.
- `order`: **+** `source` + estado/flag de "pendiente de confirmación" si el gate está ON.
- `table_session` (nueva): `tenant_id`, `table_id`, `token`/`pin`, `opened_at`, `expires_at`, estado. (Espejo del challenge de presence.)
- `advisor_settings`/config del tenant: `self_order_enabled`, `self_pay_enabled`, `self_order_requires_confirmation`.

Todo con **RLS por `tenant_id`** y migraciones incrementales (la última aplicada fue **0027** según memoria).

## 7. Decisiones abiertas (bloqueantes de producto)

1. **¿Pago antes o después de comer?** (pay-first reduce fraude pero fricciona; pay-after es lo natural en mesa). Recomendado: **pay-after** con "pedir la cuenta y pagar".
2. **¿Gate de cocina ON u OFF por default?** Recomendado: **ON** (el mozo confirma) para el rollout en AR; configurable.
3. **¿El comensal se identifica?** (nombre/teléfono opcional → CRM/loyalty, o 100% anónimo). Recomendado: **opcional**.
4. **¿Superficie del front:** ruta nueva dentro de la app (`/carta/:token`) o mini-app separada? Recomendado: **ruta en la app** (reusa build/tema/i18n).
5. **QR estático por mesa vs dinámico por sesión.** Estático (impreso) es más simple; la seguridad la da el token+PIN rotativo. Recomendado: **QR estático + PIN de mesa** que el mozo puede rotar.
6. **Modelo de modificadores:** ¿cuán complejo? (grupos anidados, reglas). Recomendado: **simple primero** (grupos con opciones y precio), sin reglas anidadas.

## 8. No-goals (por ahora)

- Reservas/turnos desde el QR (ya existe `reservations`, es otro flujo).
- Delivery/takeaway online (esto es **en-mesa**; el takeaway es una fase futura).
- Programa de puntos/loyalty completo (se apoya en CRM pero no es parte de esta feature).
- Menú con IA generativo / recomendador (fase futura; el copiloto ya existe para el dueño).

## 9. Métricas de éxito

- % de mesas que usan el QR (adopción).
- Fase 2: % de comandas originadas por `CUSTOMER_QR` vs `WAITER`.
- Fase 3: % de tickets pagados desde el celular; tiempo de rotación de mesa; ticket promedio (upsell por fotos/modificadores).
- Operativo: reducción de errores de comanda; carga del mozo.

## 10. Riesgos

- **Adopción AR** (cultura de mozo) → mitigado por el faseo (Fase 1 sola ya sirve) y el gate ON.
- **Fraude / pedir-y-rajar** → mitigado por pay-after + identificación opcional + control del mozo.
- **Flood de cocina** → gate de confirmación.
- **Fiscal:** factura por pago del cliente (quién, cómo) → reusa ARCA pero hay que diseñar el disparo.
- **Seguridad de la sesión de mesa** → token firmado + expiración + PIN rotativo + RLS.

---

## Próximo paso

Con este PRD aprobado, el siguiente artefacto es el **plan por fase** (`/prp-plan` → `.claude/PRPs/plans/`), arrancando por **Fase 1 (carta QR de solo lectura)**: sesión de mesa pública + carta bilingüe + "llamar al mozo/pedir la cuenta". Es la que más rápido deja valor y monta el plumbing para las fases 2 y 3.
