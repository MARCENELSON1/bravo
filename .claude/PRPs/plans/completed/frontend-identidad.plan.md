# Plan: Frontend de Identidad (rebanada vertical de auth)

## Summary
Conectar el frontend React existente (`src/`) con el subsistema de identidad/login ya construido en el backend (Fase 1), sentando la **arquitectura de front en capas (UI / estado / datos) que reusarán todas las fases**: clientes de API inyectables (no `fetch` suelto), TanStack Query como capa de datos, router con guard por rol, manejo de errores `{code, message}` en español y sesión segura (access token en memoria + refresh en **cookie `HttpOnly`**). Incluye un cambio chico de backend (presentación) para mover el refresh token del body a una cookie `HttpOnly`, servido bajo el mismo origen vía proxy de Vite.

## User Story
Como **dueño/encargado (OWNER/MANAGER) o empleado (WAITER/KITCHEN/CASHIER) de un local**,
quiero **crear mi comercio, verificar mi email, iniciar sesión y aceptar invitaciones desde una UI en español**,
para **acceder a las funciones que me corresponden según mi rol, con una sesión que no expone mis tokens y sobrevive a recargar la página**.

## Problem → Solution
**Hoy:** el backend de identidad está completo y validado (12 endpoints, multi-tenant, RLS), pero el frontend es la demo de Vite (`App.tsx` con un contador). No hay router, ni clientes de API, ni estado de sesión, ni pantallas. → **Después:** una rebanada vertical de identidad funcional (login, onboarding, verificar email, aceptar invitación) sobre una arquitectura de front en capas, segura y testeada, lista para que las fases 2-9 monten sus pantallas encima sin reescribir la base.

## Metadata
- **Complexity**: Large (XL en alcance arquitectónico, pero acotado por pantallas)
- **Source PRD**: `.claude/PRPs/prds/bravo-cerebro-del-local.prd.md` (es el **frontend de la Fase 1 — Fundaciones + Identidad**; el PRD ya define "Frontend en capas con clientes de API inyectables, web app responsive + RBAC", línea 132 / 260)
- **PRD Phase**: Fase 1 — Fundaciones + Identidad (porción frontend)
- **Estimated Files**: ~40 nuevos (frontend) + ~4 modificados (backend)

---

## UX Design

### Before
```
┌───────────────────────────────────────────┐
│  Demo Vite + React                          │
│  [logos]  "Get started"  [Count is 0]       │
│  Documentation / Connect with us            │
│  (sin router, sin auth, sin datos)          │
└───────────────────────────────────────────┘
```

### After (flujos)
```
PÚBLICO (sin sesión)
  /login ───────────► [Comercio (slug) · Email · Contraseña]  ── login OK ──► /app
     │  ├─ "Crear comercio" ─► /onboarding
     │  └─ error email_not_verified ─► aviso "Verificá tu email"
     │
  /onboarding ─► [Nombre · Slug · Email dueño · Contraseña] ─► "Te enviamos un email para verificar"
  /verify-email?token=… ─► (verifica al montar) ─► "Email verificado" ─► CTA /login
  /accept-invitation?token=… ─► [Contraseña] ─► "Invitación aceptada" ─► CTA /login

PROTEGIDO (con sesión)
  /app ─────────► Home placeholder: "Sesión iniciada como {ROLE}" + [Cerrar sesión]
     └─ /app/invite  (solo OWNER/MANAGER) ─► [Email · Rol] ─► "Invitación enviada"
        (WAITER/KITCHEN/CASHIER → 403 "No tenés permisos")
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Entrada a la app | Demo estática | Router; redirige a `/login` si no hay sesión | `<RequireAuth>` |
| Login | — | Form OAuth2: el **slug del comercio va en `client_id`** | `application/x-www-form-urlencoded` |
| Sesión tras recargar | — | Silent-refresh contra cookie `HttpOnly` → restaura sesión sin re-login | Sin token en JS |
| Errores de API | — | `{code,message}` → se muestra `message` (ES); `FormMessage` por campo + toast/alert global | `email_not_verified` se respeta como aviso, no error neutro |
| Acceso por rol | — | Pantalla de invitar gateada a OWNER/MANAGER | `<RequireRole>` |

---

## Mandatory Reading

Leer ANTES de implementar.

### Frontend
| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `src/components/ui/button.tsx` | all | Patrón exacto de componente (cva + `data-slot` + `cn()` + `function`/`export { }`) a imitar |
| P0 | `src/lib/utils.ts` | all | Helper `cn()` — usar siempre para clases |
| P0 | `components.json` | all | Aliases (`@/components`, `@/components/ui`, `@/lib`, `@/hooks`), style `radix-nova`, registries `@shadcn` + `@cult-ui` |
| P0 | `vite.config.ts` | all | Alias `@`; acá se agrega el **proxy** `/api → :8000` |
| P0 | `src/index.css` | all | Tokens de tema (oklch): `bg-background`, `text-foreground`, `border-border`, `--primary`, etc. (usar tokens, no colores hardcodeados) |
| P1 | `src/main.tsx` / `src/App.tsx` | all | Punto de entrada a reemplazar por el árbol de providers + router |
| P1 | `tsconfig.app.json` | all | `verbatimModuleSyntax`, `noUnusedLocals`, `erasableSyntaxOnly` → importar tipos con `import type`; sin imports sin usar |

### Backend (para el cambio de cookie — leer el código real, no asumir)
| Priority | File | Why |
|---|---|---|
| P0 | `backend/app/presentation/api/v1/auth.py` | Routers `login`/`refresh`/`logout` a modificar (setear/leer/limpiar cookie) |
| P0 | `backend/app/presentation/schemas/auth.py` | `TokenPair`, `RefreshRequest`, `LogoutRequest`, `MessageResponse` |
| P0 | `backend/app/config.py` | Settings (`pydantic-settings`); agregar config de cookie; TTL de refresh |
| P1 | `backend/app/application/identity/authenticate.py` / `refresh_token.py` / `logout.py` | Tipos de retorno de los casos de uso (no se tocan; solo presentación) |
| P1 | `backend/app/presentation/deps.py` | Cómo se inyectan los casos de uso en routers |
| P1 | `backend/tests/integration` (auth e2e) | Tests a actualizar (login ya no devuelve refresh en body) |
| P2 | `docs/architecture/backend-clean-architecture.md` | Respetar capas: el cambio vive SOLO en `presentation` |

### Contexto/decisiones
| File | Why |
|---|---|
| `CLAUDE.md` | Reglas: backend EN / UX ES; errores `{code EN, message ES}`; capas en el front |
| memory `decision-login-email-not-verified` | **No** neutralizar `email_not_verified` en login (decisión de producto fijada por test e2e) |
| memory `resume-fase-1-implementacion` | Estado de Fase 1, entorno backend, slug en `client_id`, tokens opacos `{tenant_id}.{secret}` |

---

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| react-router v7 (data router) | reactrouter.com | `createBrowserRouter` + rutas; guards como rutas con `<Outlet>` envuelto en `<RequireAuth>` |
| TanStack Query v5 | tanstack.com/query | `QueryClientProvider`, `useMutation` (login/onboarding/…), `useQuery(['me'])`; **el refresh-on-401 vive en el http-client, debajo de Query** |
| react-hook-form + zod | react-hook-form.com / zod.dev | `useForm({resolver: zodResolver(schema)})`; `FormMessage` muestra errores de validación; `setError('root', …)` para errores de servidor |
| shadcn (registro @shadcn/@cult-ui) | ui.shadcn.com | Primitivas vía MCP `mcp__shadcn__*`; `npx shadcn@latest add @shadcn/...` |
| Cookies `HttpOnly` + FastAPI | fastapi.tiangolo.com | `response.set_cookie(httponly=True, secure=True, samesite="lax", path="/api/v1/auth")`; leer con `Cookie(...)`; en `localhost` el browser permite `Secure` |

> **External research**: patrones internos bien entendidos + libs estándar. Sin investigación adicional necesaria salvo confirmar firmas de las libs al integrarlas.

---

## API Contract (fuente de la verdad — verificado contra el backend)

Base: **mismo origen vía proxy** → el front llama rutas **relativas** `/api/v1/...` (en dev el proxy de Vite las reenvía a `http://localhost:8000`).

### Roles (enum exacto)
`OWNER | MANAGER | WAITER | KITCHEN | CASHIER` — def. en `backend/app/domain/user/value_objects.py`.
Jerarquía de invitación: OWNER invita {MANAGER,WAITER,KITCHEN,CASHIER}; MANAGER invita {WAITER,KITCHEN,CASHIER}; el resto no invita.

### Endpoints que consume esta rebanada
| Método | Path | Auth | Request | Response (200/201) |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | No | **form-urlencoded**: `username`(email), `password`, `client_id`(**= tenant slug**) | `{access_token, token_type}` *(refresh → cookie)* |
| POST | `/api/v1/auth/refresh` | cookie | *(vacío; refresh va en cookie)* | `{access_token, token_type}` *(rota cookie)* |
| POST | `/api/v1/auth/logout` | cookie | *(vacío)* | `{message}` *(limpia cookie)* |
| POST | `/api/v1/tenants/onboarding` | No | JSON `{tenant_name, tenant_slug, owner_email, owner_password}` | `201 {tenant_id, user_id, message}` |
| POST | `/api/v1/auth/verify-email` | No | JSON `{token}` | `{message}` |
| POST | `/api/v1/users/accept-invitation` | No | JSON `{token, password}` | `{message}` |
| POST | `/api/v1/users/invite` | Bearer (OWNER/MANAGER) | JSON `{email, role}` (role ≠ OWNER) | `201 {message}` |
| GET | `/api/v1/ping` | Bearer | — | `{tenant_id, user_id, role}` *(whoami)* |
| POST | `/api/v1/auth/forgot-password` | No | JSON `{tenant_slug, email}` | `{message}` *(cliente sí, pantalla diferida)* |
| POST | `/api/v1/auth/reset-password` | No | JSON `{token, new_password}` | `{message}` *(cliente sí, pantalla diferida)* |
| POST | `/api/v1/auth/change-password` | Bearer | JSON `{current_password, new_password}` | `{message}` *(cliente sí, pantalla diferida)* |

> **GOTCHA `/ping`**: devuelve `{tenant_id, user_id, role}` — **no** trae email. La sesión post-refresh se hidrata desde `/ping`, así que la home muestra rol/tenant, no email.

### Validaciones de campo (reflejar en zod, mismas que el backend)
- `tenant_slug`: `^[a-z0-9-]+$`, 2–63 chars (minúsculas).
- `tenant_name`: 2–120.
- emails: formato email (EmailStr).
- passwords: 8–128.

### Error codes `{code, message}` (todos en ES para mostrar `message`)
| code | HTTP | Dónde / cómo lo maneja el front |
|---|---|---|
| `invalid_credentials` | 401 | Login: alert global "Email o contraseña incorrectos." |
| `email_not_verified` | 403 | Login: **aviso especial** "Tenés que verificar tu email antes de ingresar." (NO neutralizar) |
| `user_locked` | 423 | Login: alert "Cuenta bloqueada temporalmente…" |
| `inactive_user` | 403 | Login: alert con `message` |
| `tenant_not_found` | 404 | Login/forgot: alert con `message` |
| `tenant_already_exists` | 409 | Onboarding: error en campo slug |
| `email_already_registered` | 409 | Onboarding/invite: error en campo email |
| `invalid_email` | 422 | Onboarding/invite: error en campo email |
| `validation_error` | 422 | Form: alert con `message` ("Los datos enviados no son válidos.") |
| `invalid_token` / `expired_token` / `token_already_used` | 401/409 | verify-email/reset: estado de error con `message` |
| `invalid_invitation` | 400 | accept-invitation: estado de error "La invitación no es válida o expiró." |
| `insufficient_role` | 403 | invite: alert "No tenés permisos…" (además ya gateado por `<RequireRole>`) |

---

## Patterns to Mirror

### COMPONENT_PATTERN (shadcn + cva + cn + data-slot)
```tsx
// SOURCE: src/components/ui/button.tsx:1-67
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva("inline-flex … focus-visible:ring-ring/50 …", {
  variants: { variant: { default: "bg-primary text-primary-foreground …" } },
  defaultVariants: { variant: "default", size: "default" },
})

function Button({ className, variant = "default", ...props }: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return <button data-slot="button" data-variant={variant} className={cn(buttonVariants({ variant, className }))} {...props} />
}
export { Button, buttonVariants }
```
**Reglas que se derivan:** archivos **kebab-case**, export nombrado `export { Foo }`, componentes `function` (no `const Foo = () =>`), siempre `cn(...)`, usar tokens de tema (`bg-background`, `text-foreground`, `border-border`, `text-destructive`) — nunca colores hardcodeados. `import type` para tipos (por `verbatimModuleSyntax`).

### CN_UTIL
```ts
// SOURCE: src/lib/utils.ts:1-6
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
```

### THEME_TOKENS (usar estos, definidos en src/index.css)
`--background/--foreground`, `--primary/--primary-foreground`, `--muted/--muted-foreground`, `--destructive`, `--border`, `--input`, `--ring`, `--card`, `--radius`. Dark mode vía clase `.dark`.

### BACKEND_ROUTER_PATTERN (para el cambio de cookie — imitar el estilo de auth.py)
```python
# SOURCE: backend/app/presentation/api/v1/auth.py (router fino; el caso de uso hace el trabajo)
@router.post("/login", response_model=AccessTokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), uc: AuthenticateUser = Depends(...)):
    pair = uc.execute(slug=form.client_id, email=form.username, password=form.password)
    # NUEVO: setear refresh en cookie HttpOnly en vez de devolverlo en el body
    return _with_refresh_cookie(AccessTokenResponse(access_token=pair.access_token), pair.refresh_token)
```
**Regla:** la lógica queda en `application`; el router solo traduce HTTP↔caso de uso y ahora gestiona la cookie. Errores: ya existe el handler que mapea excepciones de dominio a `{code, message}` (`backend/app/presentation/errors.py`) — no tocar.

---

## Architecture — capas del front (lo que reusan todas las fases)

```
src/
  main.tsx                         # render(<Providers><App/></Providers>)
  App.tsx                          # <RouterProvider router={router}/>
  app/
    providers.tsx                  # QueryClientProvider → ServicesProvider → AuthProvider → <Toaster/>
    router.tsx                     # createBrowserRouter: rutas públicas + protegidas
  lib/
    utils.ts                       # (existente) cn
    env.ts                         # API_BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1"
  api/                             # ── DATOS (clientes inyectables, sin fetch suelto) ──
    api-error.ts                   # class ApiError { code: string; message: string; status: number }
    token-store.ts                 # access token EN MEMORIA (módulo, fuera de React): get/set/clear
    http-client.ts                 # HttpClient (interface/port) + FetchHttpClient (adapter): adjunta Bearer, parsea {code,message}→ApiError, refresh-on-401 single-flight
    types.ts                       # DTOs: Role, AccessTokenResponse, MeResponse, OnboardingResponse, ...
    auth-api.ts                    # AuthApi(httpClient): login/refresh/logout/me/onboarding/verifyEmail/acceptInvitation/inviteUser/forgotPassword/resetPassword/changePassword
  services/
    services-context.tsx           # DI: ServicesProvider provee { authApi } (construido desde FetchHttpClient); useServices(); override en tests
  auth/                            # ── ESTADO (sesión) ──
    session.ts                     # type Session = { userId, tenantId, role } | null
    auth-context.tsx               # AuthProvider: bootstrap (silent refresh→/ping), login(), logout(); useAuth()
    require-auth.tsx               # <RequireAuth> (redirige a /login si no hay sesión; muestra spinner durante bootstrap)
    require-role.tsx               # <RequireRole allow={Role[]}> (403 si el rol no está)
  hooks/                           # ── hooks de caso de uso (TanStack Query encima de authApi) ──
    use-login.ts use-onboarding.ts use-verify-email.ts use-accept-invitation.ts use-invite-user.ts use-me.ts
  components/
    ui/                            # shadcn (button existente + input,label,card,form,field,select,sonner,spinner)
    auth/auth-layout.tsx           # layout split-screen (Cult UI: gradient-heading / texture-card)
    form-error.tsx                 # <FormError code? message> alert global con tokens destructive
  features/identity/
    login-page.tsx onboarding-page.tsx verify-email-page.tsx accept-invitation-page.tsx
    invite-user-page.tsx home-page.tsx
  test/
    setup.ts                       # vitest + @testing-library/jest-dom
    test-utils.tsx                 # renderWithProviders(ui, { services?, route? }) con fakes inyectables
```

**Flujo de sesión (clave del diseño seguro):**
1. **Boot**: `AuthProvider` llama `authApi.refresh()` (POST `/api/v1/auth/refresh`, `credentials:'include'` → la cookie viaja). Si OK → guarda access en `tokenStore` → `authApi.me()` (`/ping`) → `Session`. Si falla → `Session=null` (no logueado). El JS nunca tuvo el refresh.
2. **Login**: `authApi.login(slug,email,pass)` → access a `tokenStore`, backend setea cookie → `me()` → `Session`.
3. **401 en cualquier request**: el `FetchHttpClient` dispara **un** refresh (single-flight, encola las demás), reintenta. Si el refresh falla → `tokenStore.clear()` + evento → `AuthProvider` pasa a `Session=null` → redirige a `/login`.
4. **Logout**: `authApi.logout()` (limpia cookie + revoca server-side) → `tokenStore.clear()` + `queryClient.clear()` → `/login`.

---

## Files to Change

### Backend (cambio chico — solo `presentation` + config + tests)
| File | Action | Justification |
|---|---|---|
| `backend/app/config.py` | UPDATE | Settings de cookie: `REFRESH_COOKIE_NAME` (def. `bravo_refresh`), `COOKIE_SECURE` (def. `True`), `COOKIE_SAMESITE` (def. `lax`), `COOKIE_PATH` (def. `/api/v1/auth`) |
| `backend/app/presentation/schemas/auth.py` | UPDATE | `AccessTokenResponse {access_token, token_type}` (login/refresh); `RefreshRequest`/`LogoutRequest` → body opcional (fallback no-browser) |
| `backend/app/presentation/api/v1/auth.py` | UPDATE | `login`: setear cookie refresh, devolver solo access. `refresh`: leer cookie (fallback body), rotar cookie. `logout`: leer cookie, limpiar cookie. Helper `_set_refresh_cookie/_clear_refresh_cookie` |
| `backend/tests/integration/*auth*` | UPDATE | Login ya no devuelve `refresh_token` en body; refresh/logout usan cookie (TestClient persiste cookies entre requests) |

### Frontend (nuevos salvo indicado)
| File | Action | Justification |
|---|---|---|
| `package.json` | UPDATE | deps: `react-router-dom`, `@tanstack/react-query`, `react-hook-form`, `@hookform/resolvers`, `zod`; devDeps: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `@vitest/coverage-v8` |
| `vite.config.ts` | UPDATE | `server.proxy['/api'] = { target: 'http://localhost:8000', changeOrigin: true }`; bloque `test` de vitest (environment jsdom, setupFiles) |
| `.env.example` (frontend, raíz) | CREATE | `VITE_API_URL=/api/v1` |
| `src/main.tsx` | UPDATE | Envolver `<App/>` en `<Providers>` |
| `src/App.tsx` | UPDATE | Reemplazar demo por `<RouterProvider router={router}/>` |
| `src/App.css` | DELETE | Estilos de la demo (ya no se usan) |
| `src/app/providers.tsx`, `src/app/router.tsx` | CREATE | Árbol de providers + rutas |
| `src/lib/env.ts` | CREATE | Acceso tipado a `VITE_API_URL` |
| `src/api/{api-error,token-store,http-client,types,auth-api}.ts` | CREATE | Capa de datos inyectable |
| `src/services/services-context.tsx` | CREATE | DI de clientes |
| `src/auth/{session,auth-context,require-auth,require-role}.{ts,tsx}` | CREATE | Estado de sesión + guards |
| `src/hooks/use-*.ts` | CREATE | Hooks de caso de uso (Query) |
| `src/components/ui/*` | CREATE (vía shadcn) | input, label, card, form, field, select, sonner, spinner |
| `src/components/auth/auth-layout.tsx`, `src/components/form-error.tsx` | CREATE | Layout + error global |
| `src/features/identity/*-page.tsx` | CREATE | 6 pantallas |
| `src/test/{setup.ts,test-utils.tsx}` | CREATE | Infra de tests |

## NOT Building (esta rebanada)
- **Pantallas** de forgot-password / reset-password / change-password (el **cliente de API sí** las cubre; las pantallas se difieren — el prompt fijó 4 pantallas). Quedan como fast-follow trivial sobre el mismo patrón.
- Migrar la cookie a un dominio cross-site con `SameSite=None` (no hace falta: mismo origen vía proxy). CSRF mitigado por `SameSite=Lax`.
- Reenvío de email de verificación (no hay endpoint de resend en el backend).
- Página real de `/app` (dashboard): solo un **placeholder** que prueba la sesión y el guard de rol. Las fases 2-9 la reemplazan.
- Endpoint `/me` con perfil completo (email/nombre): hoy se usa `/ping` (rol/tenant/user). Ampliarlo es backend futuro.
- i18n / multi-idioma (la UX es español rioplatense fijo).
- Refresh proactivo por temporizador (alcanza el reactivo on-401).

---

## Step-by-Step Tasks

### Task 1 — Backend: refresh token en cookie HttpOnly
- **ACTION**: Mover el refresh token del body a una cookie `HttpOnly` en `login`/`refresh`/`logout`. Solo capa `presentation` + config.
- **IMPLEMENT**:
  - `config.py`: agregar settings `REFRESH_COOKIE_NAME="bravo_refresh"`, `COOKIE_SECURE=True`, `COOKIE_SAMESITE="lax"`, `COOKIE_PATH="/api/v1/auth"`. Reutilizar `REFRESH_TOKEN_TTL_DAYS` para `max_age`.
  - `schemas/auth.py`: nuevo `AccessTokenResponse(access_token: str, token_type: str = "bearer")`. Hacer `RefreshRequest.refresh_token` / `LogoutRequest.refresh_token` **opcionales** (fallback para clientes no-browser).
  - `auth.py`: helpers `_set_refresh_cookie(response, token)` (`response.set_cookie(key=settings.REFRESH_COOKIE_NAME, value=token, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, path=settings.COOKIE_PATH, max_age=…)`) y `_clear_refresh_cookie(response)` (`delete_cookie` con mismo path). Inyectar `Response` en los handlers. `refresh`/`logout` leen el token con `Cookie(default=None)` y caen al body si viene.
- **MIRROR**: `BACKEND_ROUTER_PATTERN` (router fino; el caso de uso no cambia, sigue recibiendo el string del refresh token).
- **IMPORTS**: `from fastapi import Response, Cookie`; `from app.config import settings` (o como esté inyectada la config en `deps.py`).
- **GOTCHA**: en `localhost` el browser **sí** acepta cookies `Secure`. El path `/api/v1/auth` hace que la cookie solo viaje a login/refresh/logout (mínima exposición). No agregar CORS: el front va por proxy (mismo origen). No tocar `application`/`domain`.
- **VALIDATE**: `cd backend && poetry run ruff check . && poetry run mypy app`; tests del Task 2.

### Task 2 — Backend: actualizar tests de auth
- **ACTION**: Ajustar los tests de integración/e2e al nuevo contrato.
- **IMPLEMENT**: login ya no devuelve `refresh_token` en body (assert sobre `access_token` + cookie `Set-Cookie`). Para refresh/logout, usar el mismo `TestClient` (persiste cookies) o pasar el token por body (fallback). Verificar que la cookie es `HttpOnly` y se limpia en logout.
- **MIRROR**: estructura de tests existente en `backend/tests/integration`.
- **VALIDATE**: `cd backend && poetry run pytest tests/unit tests/integration -q` → verde (mantener cobertura).

### Task 3 — Frontend: deps + proxy + vitest
- **ACTION**: Instalar dependencias, configurar el proxy de Vite y Vitest.
- **IMPLEMENT**:
  - `npm i react-router-dom @tanstack/react-query react-hook-form @hookform/resolvers zod`
  - `npm i -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/coverage-v8`
  - `vite.config.ts`: `server: { proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } }` y `test: { environment: 'jsdom', globals: true, setupFiles: './src/test/setup.ts', css: false }` (usar `/// <reference types="vitest/config" />` o `defineConfig` de `vitest/config`).
  - `package.json` scripts: `"test": "vitest run"`, `"test:watch": "vitest"`, `"typecheck": "tsc -b"`.
  - `.env.example`: `VITE_API_URL=/api/v1`.
  - `src/test/setup.ts`: `import '@testing-library/jest-dom'`.
- **GOTCHA**: con el proxy, **mismo origen** → no hace falta CORS. `import.meta.env.VITE_*` solo expone vars con prefijo `VITE_`.
- **VALIDATE**: `npm run build` (debe seguir compilando); `npm run test` (0 tests aún → OK).

### Task 4 — Frontend: primitivas shadcn
- **ACTION**: Agregar las primitivas de formulario que faltan (las hay en `@shadcn`, no en `@cult-ui`).
- **IMPLEMENT**: `npx shadcn@latest add @shadcn/input @shadcn/label @shadcn/card @shadcn/form @shadcn/sonner @shadcn/field @shadcn/select @shadcn/spinner` (confirmado vía MCP `get_add_command_for_items`). Para acentos visuales del layout, evaluar `@cult-ui/gradient-heading` y `@cult-ui/texture-card` (vía MCP) — opcional, no bloqueante.
- **MIRROR**: quedan en `src/components/ui/` junto a `button.tsx`/`texture-button.tsx` con el mismo estilo.
- **GOTCHA**: `@shadcn/form` instala el wiring de react-hook-form (FormField/FormItem/FormControl/FormMessage). No reimplementar a mano. Revisar que respeten los tokens del tema (style `radix-nova`).
- **VALIDATE**: `npm run build` sin errores de tipos; los componentes importan `cn` desde `@/lib/utils`.

### Task 5 — Capa de datos: ApiError + token-store + http-client
- **ACTION**: Crear el cliente HTTP inyectable con manejo de `{code,message}` y refresh-on-401.
- **IMPLEMENT**:
  - `api-error.ts`: `export class ApiError extends Error { constructor(public code: string, message: string, public status: number) { super(message) } }`.
  - `token-store.ts`: módulo con `let accessToken: string | null`; `getAccessToken/setAccessToken/clearAccessToken`; opcional `onUnauthorized` callback que registra `AuthProvider`.
  - `http-client.ts`: `interface HttpClient { request<T>(method, path, opts): Promise<T> }`. `FetchHttpClient` implementa con `fetch(API_BASE_URL+path, { method, headers, body, credentials: 'include' })`:
    - Adjunta `Authorization: Bearer <accessToken>` si hay y la ruta lo requiere (`opts.auth`).
    - Soporta body JSON o `URLSearchParams` (form-urlencoded para login).
    - En respuesta no-2xx: parsea `{code,message}` y lanza `ApiError(code,message,status)`; si no es JSON, `ApiError('unknown', 'Ocurrió un error inesperado.', status)`.
    - **Refresh single-flight**: en 401 con `opts.auth` y no es la propia `/auth/refresh`, dispara `refreshPromise ??= doRefresh()`; espera; si OK reintenta UNA vez; si falla, `clearAccessToken()` + `onUnauthorized()` y propaga el `ApiError`.
- **MIRROR**: separación puerto/adapter (espejo del backend Ports & Adapters).
- **GOTCHA**: `credentials:'include'` para que viaje la cookie en `/auth/*`. No guardar el access token en `localStorage` (solo en `tokenStore` en memoria). No meter `fetch` fuera de esta clase.
- **VALIDATE**: test unitario (Task 11) del single-flight y del mapeo de error; `npm run build`.

### Task 6 — Capa de datos: types + AuthApi
- **ACTION**: DTOs y cliente de identidad inyectable.
- **IMPLEMENT**:
  - `types.ts`: `export type Role = 'OWNER'|'MANAGER'|'WAITER'|'KITCHEN'|'CASHIER'`; `AccessTokenResponse`, `MeResponse {tenant_id,user_id,role}`, `OnboardingResponse`, `MessageResponse`, payloads de cada request.
  - `auth-api.ts`: `class AuthApi { constructor(private http: HttpClient) {} }` con métodos:
    - `login(slug,email,password)` → `POST /auth/login` body `URLSearchParams({username:email,password,client_id:slug})`, `auth:false`. Setea `setAccessToken(res.access_token)`.
    - `refresh()` → `POST /auth/refresh`, `auth:false`, `credentials:include`; setea access.
    - `logout()` → `POST /auth/logout`.
    - `me()` → `GET /ping`, `auth:true` → `MeResponse`.
    - `onboard(data)` → `POST /tenants/onboarding`.
    - `verifyEmail(token)` → `POST /auth/verify-email`.
    - `acceptInvitation(token,password)` → `POST /users/accept-invitation`.
    - `inviteUser(email,role)` → `POST /users/invite`, `auth:true`.
    - `forgotPassword/resetPassword/changePassword` (clientes completos; sin pantalla).
- **MIRROR**: nombres EN (backend), igual que el resto del repo; archivos kebab-case.
- **GOTCHA**: el **slug va en `client_id`** (no inventar un campo nuevo). Login es form-urlencoded; el resto JSON.
- **VALIDATE**: `npm run build`; test del body de login (Task 11).

### Task 7 — DI: ServicesProvider
- **ACTION**: Inyectar `authApi` por contexto (no instanciar clientes dentro de componentes).
- **IMPLEMENT**: `services-context.tsx`: `createContext<{authApi: AuthApi}>`. `ServicesProvider` construye `new AuthApi(new FetchHttpClient(API_BASE_URL))` por defecto, pero acepta `value` override (para tests). `useServices()` con guard de "fuera de provider".
- **MIRROR**: DI por contenedor del backend (acá: contexto inyectable; fakes en tests = `override` de providers).
- **GOTCHA**: instanciar el cliente UNA vez (useMemo) para no recrearlo por render.
- **VALIDATE**: `npm run build`; un componente que llama `useServices()` fuera del provider tira error claro (test).

### Task 8 — Estado: AuthProvider + guards
- **ACTION**: Sesión en memoria, bootstrap por silent-refresh, login/logout, guards por auth y rol.
- **IMPLEMENT**:
  - `session.ts`: `type Session = { userId: string; tenantId: string; role: Role }`.
  - `auth-context.tsx`: estado `{ status: 'booting'|'authenticated'|'anonymous', session }`. En mount: `authApi.refresh().then(()=>authApi.me()).then(setSession 'authenticated').catch(()=> 'anonymous')`. Registrar `tokenStore.onUnauthorized = () => setAnonymous()`. Exponer `login(slug,email,pass)` (llama authApi.login→me), `logout()` (authApi.logout + queryClient.clear + anonymous). `useAuth()`.
  - `require-auth.tsx`: si `booting` → `<Spinner/>` full-screen; si `anonymous` → `<Navigate to="/login" state={{from}}/>`; si auth → `<Outlet/>`.
  - `require-role.tsx`: `allow: Role[]`; si `session.role` no está → página 403 "No tenés permisos para ver esto."; si sí → `<Outlet/>`.
- **MIRROR**: errores en español; tokens de tema en la página 403/spinner.
- **GOTCHA**: el bootstrap debe correr **antes** de pintar rutas protegidas (de ahí el estado `booting`). No leer email de `/ping` (no lo trae).
- **VALIDATE**: tests de guard (redirige anónimo; bloquea rol no permitido) — Task 11.

### Task 9 — Hooks de caso de uso (TanStack Query)
- **ACTION**: Envolver `authApi` en hooks de Query/Mutation; los componentes usan hooks, no `authApi` directo.
- **IMPLEMENT**: `use-me.ts` (`useQuery({queryKey:['me'], queryFn:()=>authApi.me()})`); `use-login.ts`, `use-onboarding.ts`, `use-verify-email.ts`, `use-accept-invitation.ts`, `use-invite-user.ts` (`useMutation`). Cada hook saca `authApi` de `useServices()`. En `onError`, exponer el `ApiError` para que la página decida (campo vs alert vs estado).
- **GOTCHA**: el refresh-on-401 ya vive en el http-client; **no** poner retry de Query sobre 401/403. `useMutation` por defecto no reintenta — dejarlo así.
- **VALIDATE**: `npm run build`; tests de página (Task 11) que mockean `authApi`.

### Task 10 — Pantallas + layout + router (UX español)
- **ACTION**: Construir las 6 pantallas con RHF+zod, `auth-layout`, y cablear el router.
- **IMPLEMENT**:
  - `auth-layout.tsx`: split-screen responsive (panel de marca con `gradient-heading`/tokens + panel de form en `Card`). Mobile: solo el form.
  - `login-page.tsx`: zod `{ slug, email, password }`; submit → `useLogin`. `email_not_verified` → bloque de aviso (no alert de error); `invalid_credentials`/otros → `<FormError>`. Links a `/onboarding` y (placeholder) recuperación.
  - `onboarding-page.tsx`: zod `{ tenantName, tenantSlug(regex), ownerEmail, ownerPassword }`; `tenant_already_exists`→error en slug, `email_already_registered`→error en email; success → vista "Te enviamos un email para verificar tu cuenta" + CTA `/login`.
  - `verify-email-page.tsx`: lee `?token=` con `useSearchParams`; `useEffect`→`useVerifyEmail` al montar; estados verificando/ok(CTA login)/error(`message`). Sin token → mensaje de enlace inválido.
  - `accept-invitation-page.tsx`: lee `?token=`; form `{ password }`; success "Invitación aceptada. Ya podés iniciar sesión." + CTA login; `invalid_invitation`→estado de error.
  - `invite-user-page.tsx` (protegida, dentro de `<RequireRole allow={['OWNER','MANAGER']}>`): form `{ email, role(Select sin OWNER) }` → `useInviteUser`; toast "Invitación enviada".
  - `home-page.tsx` (protegida): "Sesión iniciada como {role}" + tenant + botón Cerrar sesión; link a invitar solo si OWNER/MANAGER.
  - `router.tsx`: públicas (`/login`,`/onboarding`,`/verify-email`,`/accept-invitation`) + protegidas bajo `<RequireAuth>` (`/app` home, `/app/invite` bajo `<RequireRole>`). `*` → redirige a `/login` o `/app` según sesión.
- **MIRROR**: `COMPONENT_PATTERN`, tokens de tema, kebab-case, textos en español rioplatense.
- **GOTCHA**: respetar `decision-login-email-not-verified` (aviso, no neutralizar). El `<Select>` de rol no debe ofrecer OWNER. Mensajes de zod en español.
- **VALIDATE**: `npm run dev` → recorrer los flujos (ver Manual Validation); `npm run build`.

### Task 11 — Tests (sienta el patrón de testing del front)
- **ACTION**: Tests de alto valor sobre la lógica crítica + un par de componentes.
- **IMPLEMENT**: `test-utils.tsx` con `renderWithProviders(ui, { authApi?: Partial<AuthApi>, route? })` (inyecta fake por `ServicesProvider`, mete `MemoryRouter`, `QueryClientProvider` con retry off).
  - http-client: mapea no-2xx a `ApiError{code,message}`; refresh single-flight (dos requests 401 → un solo refresh); tras refresh fallido → `onUnauthorized` y limpia token.
  - auth-api: `login()` arma `URLSearchParams` con `client_id===slug` y setea access token.
  - guards: `<RequireAuth>` redirige anónimo a `/login`; `<RequireRole>` bloquea rol no permitido.
  - login-page: muestra el aviso de `email_not_verified`; muestra `message` en `invalid_credentials`.
- **MIRROR**: estilo behavior-first (consultar por rol/label, no por clase).
- **GOTCHA**: con fakes inyectados no se toca la red real. `QueryClient` con `retry:false` en tests.
- **VALIDATE**: `npm run test` → verde; cobertura razonable en `src/api`, `src/auth`.

### Task 12 — Limpieza + wiring final
- **ACTION**: Quitar la demo, cablear providers, smoke build.
- **IMPLEMENT**: `App.tsx`→`<RouterProvider>`; `main.tsx`→`<Providers>`; borrar `App.css` y assets de la demo no usados; `providers.tsx` arma `QueryClientProvider`→`ServicesProvider`→`AuthProvider`→`<Toaster/>`.
- **VALIDATE**: `npm run build && npm run lint && npm run test`; `npm run dev` arranca y `/login` se ve.

---

## Testing Strategy

### Unit / Component
| Test | Input | Expected | Edge? |
|---|---|---|---|
| http-client mapea error | 401 `{code:'invalid_credentials',message:'…'}` | lanza `ApiError` con code/message/status | sí |
| http-client no-JSON | 500 HTML | `ApiError('unknown', …, 500)` | sí |
| refresh single-flight | 2 requests con access vencido | 1 sola llamada a `/auth/refresh`, ambas reintentan | sí |
| refresh falla | `/auth/refresh` 401 | `onUnauthorized()` + `clearAccessToken()` | sí |
| login body | `login('mi-bar','a@b.com','x')` | body `username=a@b.com&password=x&client_id=mi-bar` | — |
| RequireAuth | session=null | `<Navigate to="/login">` | — |
| RequireRole | role=WAITER, allow=[OWNER,MANAGER] | render 403 | sí |
| login email_not_verified | mutación lanza `ApiError('email_not_verified')` | muestra aviso "verificá tu email" (no alert error) | sí |
| onboarding slug inválido | slug `Mi Bar!` | zod marca el campo (sin llamar API) | sí |

### Edge Cases Checklist
- [ ] Token en URL ausente/duplicado en verify-email / accept-invitation
- [ ] `?token=` expirado/usado → `message` correcto
- [ ] Recarga de página con cookie válida → sesión restaurada (silent refresh)
- [ ] Recarga sin cookie → cae a `/login`
- [ ] 401 en `/ping` tras vencer access → refresh transparente
- [ ] Rol no permitido en `/app/invite` → 403
- [ ] Slug con mayúsculas/espacios → zod bloquea antes de la API
- [ ] Logout limpia cookie + cache de Query + token en memoria

---

## Validation Commands

### Backend (cambio de cookie)
```bash
cd backend
poetry run ruff check . && poetry run mypy app
poetry run pytest tests/unit tests/integration -q
```
EXPECT: ruff/mypy limpios; tests verdes (cobertura mantenida).

### Frontend — Static + Tests
```bash
npm run build      # tsc -b && vite build  (typecheck + bundle)
npm run lint       # eslint .
npm run test       # vitest run
```
EXPECT: cero errores de tipos, lint limpio, tests verdes.

### Manual / E2E local
```bash
# Terminal 1
cd backend && poetry run uvicorn app.main:app --reload   # :8000  (EMAIL_TRANSPORT=console → el link sale por consola)
# Terminal 2
npm run dev                                              # :5173 (proxy /api → :8000)
```
- [ ] `/onboarding`: crear comercio → ver mensaje de "verificá tu email"; copiar el link de la consola del backend.
- [ ] `/verify-email?token=…` (del log) → "Email verificado".
- [ ] `/login` con slug+email+pass → entra a `/app` (rol OWNER).
- [ ] Recargar `/app` → sigue logueado (silent refresh por cookie).
- [ ] `/app/invite` (OWNER) → invitar WAITER → "Invitación enviada"; tomar link de la consola.
- [ ] `/accept-invitation?token=…` → setear pass → "Ya podés iniciar sesión".
- [ ] Login con el invitado → entra; `/app/invite` con WAITER → 403.
- [ ] DevTools → la cookie `bravo_refresh` es `HttpOnly` y no hay tokens en `localStorage`.
- [ ] Cerrar sesión → vuelve a `/login` y la cookie se borra.

---

## Acceptance Criteria
- [ ] Las 4 pantallas (login, onboarding, verificar email, aceptar invitación) + home protegida + invitar funcionan contra el backend real.
- [ ] Access token solo en memoria; refresh solo en cookie `HttpOnly`; sin tokens en `localStorage`/`sessionStorage`.
- [ ] Silent refresh restaura la sesión al recargar; refresh-on-401 transparente.
- [ ] Guard por auth y por rol operativos (OWNER/MANAGER vs resto en invitar).
- [ ] Errores `{code,message}` mostrados en español; `email_not_verified` respetado como aviso.
- [ ] Login manda el slug en `client_id` (form-urlencoded).
- [ ] Clientes de API inyectables (DI por contexto); sin `fetch` suelto en componentes.
- [ ] `npm run build` / `lint` / `test` verdes; backend ruff/mypy/pytest verdes.

## Completion Checklist
- [ ] Código sigue `COMPONENT_PATTERN` (kebab-case, `cn`, tokens de tema, `import type`)
- [ ] Capas separadas UI / estado (auth) / datos (api) — sin fugas
- [ ] Manejo de error uniforme vía `ApiError`
- [ ] Tests de la lógica crítica (http-client, guards, login)
- [ ] Sin valores hardcodeados (API base por env; textos ES centralizables)
- [ ] Backend: cambio confinado a `presentation` + config
- [ ] Autocontenido — sin necesidad de buscar en el código durante la implementación

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cookie `Secure` no setea en dev | Baja | Media | `localhost` es contexto seguro en Chrome/FF; si falla en Safari, `COOKIE_SECURE=False` en dev por env |
| CSRF sobre `/auth/refresh` (cookie) | Baja | Media | `SameSite=Lax` + path scope; respuesta no legible cross-origin. Doble-token CSRF = hardening futuro |
| Romper tests e2e del backend al quitar refresh del body | Media | Baja | Task 2 los actualiza; `TestClient` persiste cookies |
| Versiones nuevas (React 19 / RR v7 / TS 6 / Tailwind v4) con APIs cambiadas | Media | Media | Confirmar firmas vía MCP/docs al integrar; build como red de seguridad |
| `/ping` no trae email → UX espera nombre | Baja | Baja | Home muestra rol/tenant; `/me` con perfil es backend futuro |
| Scope creep (forgot/reset/change UI) | Media | Baja | Explícitamente fuera; cliente listo, pantalla diferida |

## Notes
- Este plan es la **porción frontend de la Fase 1** del PRD (no una fase nueva). Deja sentada la arquitectura de front (UI/estado/datos + DI + guards + testing) que reutilizan las fases 2-9.
- Convención respetada: **código en inglés** (nombres, archivos, DTOs), **UX en español**; errores `{code EN, message ES}`.
- La elección de **cookie HttpOnly** (sobre localStorage/memoria) es decisión explícita del dueño en esta sesión; coincide con el rumbo que ya marcaba el README del backend.
- Cabo suelto independiente: el **PR de Fase 1** (backend) sigue sin crearse; no bloquea esta rebanada.
