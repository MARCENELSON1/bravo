# Plan: Fase 3.5 — Conexión de cuentas de pago por tenant (MercadoPago OAuth)

## Summary
Hace que **cada tenant cobre con su propia cuenta de MercadoPago**. Hoy (Fase 3) la pasarela usa **un único** `MP_ACCESS_TOKEN` global del `.env`: la atribución interna (qué `Payment`/comanda es de qué tenant) ya es multi-tenant, pero **la plata caería siempre en la misma cuenta**. Este slice agrega el flujo **OAuth "Conectar con MercadoPago"** por tenant: el local autoriza a NÚCLEO, guardamos sus tokens **cifrados y scopeados por `tenant_id`** (RLS), y la pasarela **resuelve las credenciales del tenant en runtime** al cobrar. Opcionalmente NÚCLEO retiene un `marketplace_fee` (comisión SaaS). No toca el dominio de `Payment` ni los casos de uso de cobro: solo cambia **de dónde sale el token**.

> **DECISIÓN DE ALCANCE:** modelo **OAuth / marketplace** (recomendado), no "token pegado a mano". El **webhook secret sigue siendo a nivel app** (`MP_WEBHOOK_SECRET`, env) — **solo el access token pasa a ser por-tenant**. Se mantiene un **modo de transición**: si un tenant no tiene cuenta conectada, la pasarela cae al `MP_ACCESS_TOKEN` global del env (sandbox/single-account), así lo de Fase 3 sigue andando sin romper.

> **Prerrequisitos (los provee el usuario):**
> 1. **App MP de NÚCLEO con OAuth habilitado**: `MP_CLIENT_ID` + `MP_CLIENT_SECRET`, **redirect URI** registrada (`{API}/api/v1/integrations/mercadopago/callback`), scopes `offline_access read write`. (Crear con `create_application` del MCP o desde el panel.)
> 2. **Clave de cifrado** para tokens en reposo: `CREDENTIALS_ENCRYPTION_KEY` (Fernet, 32 bytes url-safe base64) — **solo env / secret manager, nunca al repo**.
> 3. La API exacta de OAuth de MP (endpoints `/oauth/token`, authorize URL, `/users/me`, campos `user_id`/`refresh_token`/`expires_in`) se **consulta desde el MCP** (`search_documentation`) durante la implementación — **no inventar la API**.

## Estado de implementación — ✅ COMPLETA (backend + frontend)
Implementada en `feat/fase-3-cobro-pagos` por tramos:
- **T1 `cecd528`** — fundación: `PaymentCredential` + cifrado Fernet + tabla `payment_credentials` (migración 0004 RLS) + repo/errores.
- **T2+T3 `a0e8f10`** — OAuth client (authorize/token/refresh/users-me) + use cases connect/callback/disconnect/status con state firmado; resolver por tenant (descifra, refresca on-expiry, fallback env); gateway cobra con el token del tenant (+ marketplace_fee).
- **T4 `433c389`** — API `integrations/mercadopago` (connect/callback/status/disconnect) + ruteo del webhook por `user_id→tenant`; cipher lazy; e2e del connect.
- **T5 `14d96d7`** — frontend: `IntegrationsPage` (conectar/estado/desconectar) + cliente/hook + nav.

96 tests backend + 20 front. **Falta (no bloqueante):** app MP con OAuth (`MP_CLIENT_ID/SECRET` + redirect) y `CREDENTIALS_ENCRYPTION_KEY` para prueba en vivo; y, para multi-tenant real, una sesión RLS-exenta para `get_by_account_id` del webhook (hoy cae al token app).

## User Story
Como **dueño (OWNER) / encargado (MANAGER)** quiero **vincular la cuenta de MercadoPago de mi local a NÚCLEO una sola vez**, para que **los cobros por MercadoPago/QR caigan en mi propia cuenta** (y no en una cuenta compartida), manteniendo la comanda conciliada igual que hoy.

## Problem → Solution
Hoy el token de MP es global (una cuenta para toda la plataforma). → El tenant hace **OAuth** y guardamos su `access_token`+`refresh_token` **cifrados por tenant**. Al cobrar, la pasarela **resuelve el token del `payment.tenant_id`** (refrescándolo si venció) y crea la preferencia **en nombre del vendedor**; la plata va a su cuenta. Si el tenant no conectó MP, el cobro online se rechaza con un error claro (`payment_gateway_not_connected`) o, en dev, cae al token global.

## Metadata
- **Complexity**: **L** (sin tocar dominio de pagos; sí dominio nuevo `PaymentCredential` + cripto + OAuth + 1 migración RLS + integraciones UI). Partible backend↔frontend.
- **Source PRD**: `.claude/PRPs/prds/nucleo.prd.md` (Fase 3 — Cobro + Pagos; este es su complemento de producción multi-tenant)
- **PRD Phase**: Fase 3.5 — Conexión de cuentas de pago
- **Estimated Files**: ~24 (≈17 backend, ≈7 frontend)
- **Depends on**: Fase 3 (PaymentGateway, MercadoPagoGateway, webhook)

---

## UX Design

### Before
El cobro por MP usa una cuenta única (env). No hay forma de que un local conecte la suya.

### After
Nueva pantalla **Integraciones** (`/app/integrations`, OWNER/MANAGER):
- Card **MercadoPago**: estado **"No conectado"** con botón **"Conectar con MercadoPago"** → redirige a MP (OAuth) → vuelve a la pantalla con **"Conectado a {nickname / user_id}"** + botón **"Desconectar"**.
- En la comanda, si el local **no** tiene MP conectado y el cajero elige MERCADOPAGO/QR → hint **"Conectá MercadoPago en Integraciones"** (deshabilita el cobro online; efectivo/tarjeta/transferencia siguen).

### Interaction Changes
| Antes | Después | Nota |
|---|---|---|
| Token MP global | Token MP **por tenant** (OAuth, cifrado) | la plata va a la cuenta del local |
| Cobro online siempre disponible | Requiere **MP conectado** (o fallback dev) | error `payment_gateway_not_connected` si falta |
| Webhook consulta el pago con token global | Webhook resuelve el token por **`user_id → tenant`** | secret del webhook sigue a nivel app |

---

## Mandatory Reading
### Backend — molde (Fase 3)
- `app/infrastructure/payments/mercadopago_gateway.py` — adapter httpx actual (charge/preference, verify_signature, fetch_status). **Evoluciona** para resolver token por tenant.
- `app/domain/payment/ports.py` — `PaymentGateway`, `PaymentNotificationGateway`, `GatewayChargeStatus`.
- `app/container.py` — `providers.Selector` (email/pagos) y `mercadopago_gateway` singleton.
- `app/infrastructure/security/tenant_context.py` + `app/context.py` — cómo setear el tenant sin token (lo usa el webhook).
- `alembic/versions/0003_payments.py` — molde de migración con `ENABLE/FORCE RLS` + policy `tenant_isolation`.
- `app/config.py` — settings + validación `_reject_insecure_production`.

### Frontend — molde (Fase 3)
- `src/api/payments-api.ts`, `src/hooks/use-payments.ts`, `src/services/services-{context,provider}` — cliente inyectable + hooks + DI.
- `src/features/products/products-page.tsx` — molde de pantalla con `RequireRole` (OWNER/MANAGER).
- `src/app/router.tsx`, `src/features/identity/home-page.tsx` — ruteo + nav.

## External Documentation
> Consultar vía **MCP `mercadopago`** (`search_documentation`) — no inventar:
- OAuth: authorize URL (`/authorization`), `POST /oauth/token` (`authorization_code` y `refresh_token`), campos `access_token`/`refresh_token`/`expires_in`/`user_id`/`public_key`, scopes (`offline_access read write`).
- `GET /users/me` (obtener `id`/`nickname` del vendedor para mostrar y para el ruteo del webhook).
- Marketplace: `marketplace_fee` / `application_fee` en la preferencia; cómo llega `user_id` en la notificación del webhook a nivel app.

---

## Patterns to Mirror

### CREDENTIAL_DOMAIN
```python
# app/domain/payment/credentials.py — MIRROR: Payment entity (dataclass) + StrEnum
class PaymentProvider(StrEnum):
    MERCADOPAGO = "MERCADOPAGO"

class ConnectionStatus(StrEnum):
    CONNECTED = "CONNECTED"; DISCONNECTED = "DISCONNECTED"

@dataclass
class PaymentCredential:
    tenant_id: str
    provider: PaymentProvider
    external_account_id: str          # mp user_id del vendedor (para ruteo webhook)
    nickname: str | None
    access_token: str                 # SIEMPRE cifrado en reposo (claro solo en memoria)
    refresh_token: str | None
    public_key: str | None
    expires_at: datetime | None
    live_mode: bool                   # TEST vs prod (según el token)
    status: ConnectionStatus = ConnectionStatus.CONNECTED
```

### CIPHER_PORT (cifrado de tokens en reposo)
```python
# app/domain/shared/ports.py (o payment/ports.py) — port; adapter en infrastructure
class TokenCipher(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> str: ...
    @abstractmethod
    def decrypt(self, ciphertext: str) -> str: ...
# Adapter: app/infrastructure/security/fernet_cipher.py (cryptography.Fernet, key del env)
```

### CREDENTIALS_RESOLVER (lo que usa la pasarela)
```python
# app/domain/payment/ports.py — NUEVO port
@dataclass(frozen=True)
class ResolvedCredentials:
    access_token: str
    live_mode: bool

class PaymentCredentialsResolver(ABC):
    """Devuelve el access token VIGENTE del tenant (refresca y persiste si venció).
    Lanza PaymentGatewayNotConnected si el tenant no conectó (sin fallback)."""
    @abstractmethod
    async def for_tenant(self, tenant_id: str) -> ResolvedCredentials: ...
    @abstractmethod
    async def tenant_for_account(self, external_account_id: str) -> str | None: ...
```

### GATEWAY_EVOLUTION
```python
# mercadopago_gateway.py — el constructor ya NO recibe access_token fijo.
# Recibe un PaymentCredentialsResolver + el client_id/secret/fee/env-fallback.
# charge(): creds = await resolver.for_tenant(payment.tenant_id) → cliente httpx con ESE token.
#           si hay marketplace_fee → agregarlo a la preferencia.
# fetch_status(): el webhook ya resolvió el tenant (por user_id) y pasa el token.
```

### OAUTH_USE_CASES
```python
# app/application/payment/connect_mercadopago.py
# StartConnection(tenant_id) -> authorize_url   (state firmado HMAC: tenant_id+nonce+exp)
# CompleteConnection(code, state) -> valida state, exchange code, GET /users/me,
#                                    cifra y guarda PaymentCredential, set tenant_context(state.tenant)
# DisconnectConnection(tenant_id), GetConnectionStatus(tenant_id)
```

---

## Files to Change

### Backend
| File | Action |
|---|---|
| `app/domain/payment/credentials.py` | CREATE — `PaymentCredential`, `PaymentProvider`, `ConnectionStatus` |
| `app/domain/payment/ports.py` | UPDATE — `PaymentCredentialsResolver`, `ResolvedCredentials`, `OAuthPaymentProvider` (authorize_url/exchange/refresh) |
| `app/domain/payment/repository.py` (o nuevo `credentials_repository.py`) | CREATE — `PaymentCredentialRepository` (get_by_tenant, get_by_account_id, upsert, delete) |
| `app/domain/payment/exceptions.py` | UPDATE — `PaymentGatewayNotConnected`(409), `InvalidOAuthState`(400) |
| `app/domain/shared/ports.py` | CREATE/UPDATE — `TokenCipher` port |
| `app/infrastructure/security/fernet_cipher.py` | CREATE — `FernetTokenCipher` (cryptography) |
| `app/infrastructure/payments/mercadopago_oauth.py` | CREATE — `MercadoPagoOAuthClient` (authorize URL, `/oauth/token`, `/users/me`) |
| `app/infrastructure/payments/mercadopago_gateway.py` | UPDATE — resolver token por tenant + `marketplace_fee` |
| `app/infrastructure/payments/credentials_resolver.py` | CREATE — `DbPaymentCredentialsResolver` (lee repo, descifra, refresca/persiste, fallback env) |
| `app/infrastructure/persistence/models.py` | UPDATE — `PaymentCredentialORM` (tokens cifrados, `external_account_id` index, `expires_at`) |
| `app/infrastructure/persistence/mappers.py` | UPDATE — `payment_credential_to_domain/_to_orm` |
| `app/infrastructure/persistence/credentials_repo.py` | CREATE — `SqlAlchemyPaymentCredentialRepository` (tenant-scoped) |
| `alembic/versions/0004_payment_credentials.py` | CREATE — tabla + ENABLE/FORCE RLS + policy + GRANT |
| `app/application/payment/connect_mercadopago.py` | CREATE — Start/Complete/Disconnect/Status |
| `app/presentation/schemas/integrations.py` | CREATE — `ConnectionStatusResponse`, `ConnectUrlResponse` |
| `app/presentation/api/v1/integrations.py` | CREATE — connect / callback / status / disconnect |
| `app/presentation/api/v1/webhooks.py` | UPDATE — resolver token por `user_id → tenant` antes de `fetch_status` |
| `app/presentation/errors.py` | UPDATE — registrar nuevos errores |
| `app/config.py` | UPDATE — `MP_CLIENT_ID/SECRET`, `MP_OAUTH_REDIRECT_URI`, `MP_MARKETPLACE_FEE`, `CREDENTIALS_ENCRYPTION_KEY`; deprecar `MP_ACCESS_TOKEN` a fallback dev |
| `app/container.py`, `app/main.py`, `.env.example` | UPDATE — cipher + oauth client + resolver + use cases + router; vars |
| `pyproject.toml` | UPDATE — `cryptography` |
| `tests/unit/test_credentials.py`, `test_mercadopago_oauth.py` | CREATE — cipher roundtrip, state firmado, oauth client (MockTransport), resolver (refresh) |
| `tests/integration/test_e2e_integrations.py` | CREATE — connect (fake OAuth) → status conectado → cobro usa token del tenant → RLS de credenciales |

### Frontend
| File | Action |
|---|---|
| `src/api/types-operations.ts` | UPDATE — `MpConnectionDTO` |
| `src/api/integrations-api.ts` | CREATE — `getStatus()`, `getConnectUrl()`, `disconnect()` |
| `src/services/services-{context,provider}` | UPDATE — `integrationsApi` |
| `src/hooks/use-integrations.ts` | CREATE — `useMpConnection`, `useDisconnectMp` |
| `src/features/integrations/integrations-page.tsx` | CREATE — card MP (conectar/estado/desconectar) |
| `src/features/orders/order-page.tsx` | UPDATE — hint "Conectá MercadoPago" si no conectado y método online |
| `src/app/router.tsx`, `src/features/identity/home-page.tsx`, `src/api/integrations-api.test.ts` | UPDATE/CREATE — ruta + nav + test |

## NOT Building
- **Token MP pegado a mano** (modelo no-OAuth) — descartado.
- **QR interoperable T3.0 / Payway/posnet** — siguen diferidos (Fase 3).
- **Egresos/money-out reales por MP** (transferencias salientes) — fuera de alcance.
- **Secret manager** (Vault/KMS) — por ahora la `CREDENTIALS_ENCRYPTION_KEY` va por env; migrar en prod es follow-up.
- **Rotación/cron de refresh proactivo** — se refresca *on-demand* (al cobrar, si venció). Cron opcional después.
- **Multi-pasarela genérica** (Stripe/otros) — el port queda listo, pero solo se implementa MercadoPago.

---

## Step-by-Step Tasks

> Orden: cripto → dominio credenciales → persistencia+migración → OAuth client → resolver+gateway → use cases → API+webhook → tests → frontend. Validar (`ruff/mypy/pytest`, `tsc/lint/test/build`) por bloque. Mismos patrones que Fase 3.

### Task 1 — Cifrado de tokens (`TokenCipher`)
- **IMPLEMENT**: port `TokenCipher` + adapter `FernetTokenCipher` (`cryptography.fernet`, clave de `CREDENTIALS_ENCRYPTION_KEY`); agregar `cryptography` a `pyproject`. `config.py`: la clave; validar presencia en no-dev.
- **GOTCHA**: nunca loguear tokens; descifrar solo en memoria, al momento de usar.
- **VALIDATE**: `pytest tests/unit/test_credentials.py::test_cipher_roundtrip`; `mypy app`.

### Task 2 — Dominio `PaymentCredential` + ports + errores
- **IMPLEMENT**: `credentials.py` (entidad + enums); `PaymentCredentialRepository` (get_by_tenant, get_by_account_id, upsert, delete); ports `OAuthPaymentProvider` + `PaymentCredentialsResolver` (+ `ResolvedCredentials`); errores `PaymentGatewayNotConnected`/`InvalidOAuthState`; registrarlos en `errors.py`.
- **MIRROR**: `CREDENTIAL_DOMAIN`, `CREDENTIALS_RESOLVER`; `Payment`/`PaymentRepository`.
- **VALIDATE**: `mypy app`.

### Task 3 — Persistencia + migración 0004 (RLS)
- **IMPLEMENT**: `PaymentCredentialORM` (id, tenant_id FK, provider, `external_account_id` index, nickname, `access_token`/`refresh_token` Text **cifrados**, public_key, expires_at, live_mode, status, timestamps); mapper; `SqlAlchemyPaymentCredentialRepository` (filtra tenant_id; `get_by_account_id` **sin** filtro de tenant pero solo lo usa el webhook para resolver el tenant → documentar). Migración `0004_payment_credentials` (down_revision `0003_payments`) con `ENABLE/FORCE RLS` + policy `tenant_isolation` + GRANT.
- **MIRROR**: `0003_payments.py`, `payment_repo.py`, `models.py`.
- **GOTCHA**: `get_by_account_id` corre en el webhook (sin tenant aún). Opciones: (a) consulta con rol admin/bypass acotada a ese lookup, o (b) policy que permita SELECT por `external_account_id`. Resolver en la task (preferir (a): el webhook setea tenant *después* de resolverlo).
- **VALIDATE**: `alembic upgrade head` → `downgrade -1` → `upgrade head`.

### Task 4 — `MercadoPagoOAuthClient`
- **IMPLEMENT**: authorize URL (client_id, redirect_uri, scopes, `state`), `POST /oauth/token` (`authorization_code` y `refresh_token`), `GET /users/me`. httpx, `transport` inyectable para tests. Endpoints/campos **del MCP**.
- **MIRROR**: `MercadoPagoGateway` (estructura httpx + MockTransport).
- **VALIDATE**: `pytest tests/unit/test_mercadopago_oauth.py` (exchange + refresh + parse de `user_id`, vía MockTransport).

### Task 5 — Resolver por tenant + evolución del gateway
- **IMPLEMENT**: `DbPaymentCredentialsResolver.for_tenant()` (lee repo → descifra → si `expires_at` vencido, refresca con el OAuth client y **persiste** los tokens rotados; si no hay credencial → `PaymentGatewayNotConnected`, salvo **fallback** al `MP_ACCESS_TOKEN` env en dev). `tenant_for_account()` para el webhook. `MercadoPagoGateway` deja de recibir token fijo: en `charge()` hace `resolver.for_tenant(payment.tenant_id)` y arma el cliente con ese token; agrega `marketplace_fee` si está configurado. `fetch_status()` recibe el token ya resuelto.
- **MIRROR**: `GATEWAY_EVOLUTION`; Selector del container.
- **GOTCHA**: refresh single-flight por tenant para no rotar dos veces en paralelo. Sandbox: `live_mode=False` → `sandbox_init_point`.
- **VALIDATE**: `pytest tests/unit` (resolver refresca y persiste; gateway usa el token del tenant — fakes/MockTransport).

### Task 6 — Use cases OAuth + state firmado
- **IMPLEMENT**: `StartConnection` (authorize_url con state HMAC = tenant_id+nonce+exp, firmado con `jwt_secret`/clave dedicada), `CompleteConnection` (valida/expira state → `exchange_code` → `/users/me` → cifra+upsert credencial; `tenant_context.set(state.tenant)`), `DisconnectConnection`, `GetConnectionStatus`.
- **MIRROR**: `OAUTH_USE_CASES`; `token_service` para firmar/verificar state.
- **GOTCHA**: state de un solo uso/expirable (anti-CSRF); validar que el `redirect_uri` y el `client_id` matcheen; no confiar en el `state` sin verificar la firma.
- **VALIDATE**: `pytest tests/unit/test_credentials.py` (state válido/alterado/expirado).

### Task 7 — API Integraciones + webhook por-tenant + wiring
- **IMPLEMENT**: router `integrations` — `GET /integrations/mercadopago/connect` (OWNER/MANAGER → `ConnectUrlResponse`), `GET /integrations/mercadopago/callback` (valida state, completa, **redirect 302** a `{APP_BASE_URL}/app/integrations?mp=ok|error`), `GET /integrations/mercadopago` (status), `DELETE /integrations/mercadopago`. **Webhook**: antes de `fetch_status`, leer `user_id` de la notificación → `resolver.tenant_for_account(user_id)` → `tenant_context.set(tenant)` → resolver token → fetch → conciliar (cross-check con el `external_reference`). Container: cipher + oauth client + resolver + use cases; `main.py` include_router; `config`/`.env.example` con las vars nuevas.
- **MIRROR**: `payments.py`/`webhooks.py`/`container.py`/`main.py`.
- **GOTCHA**: el callback es semi-público: su única auth es el **state firmado** (el usuario viene redirigido desde MP, sin Bearer). No exponer tokens en la URL de redirect ni en logs.
- **VALIDATE**: `ruff && mypy app`; app levanta; OpenAPI muestra los endpoints.

### Task 8 — Tests backend (e2e + integración)
- **IMPLEMENT**: override del `OAuthPaymentProvider` con un fake (devuelve tokens TEST + user_id) → `connect`/`callback` → `status` conectado → **cobro online usa el token del tenant** (assert vía fake gateway que recibió esas creds) → **RLS**: otro tenant no ve la credencial; webhook rutea por `user_id`. `conftest._TABLES += "payment_credentials"`.
- **MIRROR**: `test_e2e_payments.py`, `test_e2e_webhook.py`.
- **VALIDATE**: `pytest tests/unit tests/integration -q`.

### Task 9 — Frontend: Integraciones + hint en cobro
- **IMPLEMENT**: `integrations-api` (status/connectUrl/disconnect) + DI; `use-integrations`; `IntegrationsPage` (`/app/integrations`, RequireRole OWNER/MANAGER): estado + botón "Conectar" (`window.location = connectUrl`) + "Desconectar"; al volver con `?mp=ok` → toast + invalidar status. En `order-page`: si `!connected` y método ∈ {MERCADOPAGO, QR} → hint/deshabilitar. Nav en home (OWNER/MANAGER). Test de `integrations-api`.
- **MIRROR**: `products-page.tsx`, `payments-api.ts`/`use-payments.ts`.
- **VALIDATE**: `npm run typecheck && lint && test && build`.

### Task 10 — Cierre + validación manual
- **IMPLEMENT**: `.env.example` documentado; README de "Conectar MercadoPago". Prueba en **sandbox** con **dos** cuentas de test distintas: cada tenant conecta la suya, cada cobro cae en su cuenta; webhook confirma → comanda PAID.
- **VALIDATE**: backend + frontend verdes; flujo OAuth de punta a punta en sandbox.

---

## Validation Gates
- **Backend**: `ruff check .` · `mypy app` · `pytest tests/unit tests/integration -q` (cipher roundtrip; state firmado; oauth exchange/refresh; resolver refresca+persiste; gateway usa token del tenant; RLS de credenciales; webhook rutea por user_id) · `alembic upgrade/downgrade/upgrade` (0004).
- **Frontend**: `npm run typecheck && lint && test && build`.
- **Manual (sandbox)**: 2 tenants × 2 cuentas MP de test → cada cobro a su cuenta; desconectar/reconectar; cobro online bloqueado si no conectado.

## Risks / Open
- **Webhook chicken-egg** (para leer `external_reference` hay que consultar el pago, que necesita token): se resuelve mapeando `user_id → tenant` desde la notificación a nivel app. Confirmar en el MCP que la notificación trae `user_id`.
- **Custodia de tokens**: cifrado Fernet con clave en env (rotar la clave = re-cifrar). Migrar a secret manager en prod (follow-up).
- **Refresh races**: single-flight por tenant.
- **Modo de transición**: el fallback al `MP_ACCESS_TOKEN` global debe **deshabilitarse en prod** (validación en `config`) para no cobrar a la cuenta equivocada por error.
- **Prereq del usuario**: app MP con OAuth + redirect URI exacta + scopes; sin eso el flujo no corre.
