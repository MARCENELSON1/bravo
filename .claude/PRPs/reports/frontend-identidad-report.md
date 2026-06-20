# Implementation Report: Frontend de Identidad

## Summary
Rebanada vertical de identidad: el frontend React (`src/`) ahora consume el subsistema
de auth de la Fase 1 con una arquitectura en capas (UI / estado / datos) reutilizable por
todas las fases. Pantallas: login, onboarding, verificar email, aceptar invitación, +
home protegida e invitar usuario (gateado OWNER/MANAGER). Sesión segura: access token en
memoria + refresh en **cookie `HttpOnly`** (cambio chico de backend), servido bajo el
mismo origen vía proxy de Vite. Capa de datos con TanStack Query sobre clientes de API
inyectables (DI por contexto). Errores `{code, message}` en español.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Large | Large |
| Confidence | 8/10 | Implementado en una pasada |
| Files Changed | ~40 nuevos + ~4 backend | 36 nuevos + 12 modificados |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Backend: refresh en cookie HttpOnly | ✅ | Solo `presentation` + config; casos de uso intactos |
| 2 | Backend: tests de auth | ✅ | e2e usa cookie; `conftest` pasa a `https://test` |
| 3 | Deps + proxy Vite + Vitest | ✅ | proxy `/api`→:8000; scripts test/typecheck |
| 4 | Primitivas shadcn | ✅ | Llegó `field` (no `form`) → RHF directo |
| 5 | ApiError + token-store + http-client | ✅ | refresh-on-401 single-flight |
| 6 | types + AuthApi | ✅ | login form-urlencoded con slug en `client_id` |
| 7 | DI: ServicesProvider | ✅ | Dividido en context(.ts)+provider(.tsx) |
| 8 | AuthProvider + guards | ✅ | Dividido en context(.ts)+provider(.tsx) |
| 9 | Hooks (TanStack Query) | ✅ | use-login/onboarding/verify/accept/invite |
| 10 | Pantallas + layout + router | ✅ | 6 pantallas, RequireAuth/RequireRole |
| 11 | Tests del front | ✅ | 9 tests (http-client, auth-api, guards, login) |
| 12 | Limpieza + wiring + validación | ✅ | Providers cableados; demo borrada |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static (tsc) | ✅ Pass | `tsc -b` sin errores |
| Lint (eslint) | ✅ Pass | 0 errores |
| Unit tests (front) | ✅ Pass | 9/9 (vitest) |
| Build | ✅ Pass | `tsc -b && vite build` ok (bundle ~575kB, warning de tamaño no bloqueante) |
| Backend ruff/mypy | ✅ Pass | limpios (68 archivos) |
| Backend tests | ✅ Pass | 52/52 (43 unit + 9 integración con Postgres real) |
| Integración live (2 servers) | ⏳ Manual | Checklist en el plan; no ejecutado en esta pasada |

## Files Changed

**Backend (modificados):** `app/config.py` (settings de cookie + guard), `app/presentation/schemas/auth.py` (`AccessTokenResponse`, body opcional), `app/presentation/api/v1/auth.py` (cookie en login/refresh/logout), `tests/integration/conftest.py` (`https://test`), `tests/integration/test_e2e_auth.py`.

**Frontend (nuevos):** `src/api/{api-error,token-store,http-client,types,auth-api}.ts` + tests; `src/services/{services-context.ts,services-provider.tsx}`; `src/auth/{session.ts,auth-context.ts,auth-provider.tsx,require-auth.tsx,require-role.tsx,guards.test.tsx}`; `src/hooks/use-*.ts` (5); `src/features/identity/*-page.tsx` (6) + `login-page.test.tsx`; `src/app/{providers.tsx,router.tsx}`; `src/components/{form-error.tsx,auth/auth-layout.tsx}`; `src/components/ui/*` (input, label, card, field, select, sonner, spinner, separator, button-variants); `src/lib/{env.ts,role-labels.ts}`; `src/test/{setup.ts,test-utils.tsx}`; `.env.example`.

**Frontend (modificados):** `package.json`, `vite.config.ts`, `src/main.tsx`, `src/App.tsx`, `src/components/ui/button.tsx`, `src/App.css` (borrado).

## Deviations from Plan
1. **`@shadcn/form` no existe en el estilo `radix-nova`**; shadcn instaló `field` (la primitiva nueva). Se usó **react-hook-form directo + `field`** en vez del wrapper `<Form>` RHF. Resultado equivalente y más simple.
2. **Context dividido en dos archivos** (`*-context.ts` con hook + `*-provider.tsx` con el componente) para satisfacer `react-refresh/only-export-components` sin tocar la config de ESLint (protegida por hook). Misma API pública.
3. **`buttonVariants` extraído** a `button-variants.ts` por la misma regla (la `eslint.config.js` no se puede modificar). `button.tsx` ahora exporta solo `Button`; nada más importaba `buttonVariants`.
4. Pantallas de forgot/reset/change-password **diferidas** (el cliente `AuthApi` sí las cubre) — tal como se acotó en el plan.

## Issues Encountered
- **Cookie `Secure` sobre `http` en tests**: httpx no reenvía cookies `Secure` sobre `http`. Resuelto cambiando el `base_url` del cliente de test a `https://test` (refleja prod). 
- **`erasableSyntaxOnly` (TS)**: prohíbe parameter-properties en clases; se declararon los campos explícitamente en `ApiError`, `FetchHttpClient` y `AuthApi`.
- **`eslint.config.js` protegido por hook**: en vez de bajar la regla, se reestructuró la fuente (deviations 2 y 3).

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `src/api/http-client.test.ts` | 4 | mapeo `{code,message}`, no-JSON, single-flight, refresh fallido → onUnauthorized |
| `src/api/auth-api.test.ts` | 1 | login manda slug en `client_id` + guarda access token |
| `src/auth/guards.test.tsx` | 2 | RequireAuth redirige anónimo; RequireRole bloquea rol |
| `src/features/identity/login-page.test.tsx` | 2 | aviso `email_not_verified`; `message` en `invalid_credentials` |

## Security posture
- Access token **solo en memoria**; refresh **solo en cookie `HttpOnly`+Secure+SameSite=Lax** (path `/api/v1/auth`). Sin tokens en `localStorage`/`sessionStorage`.
- Mismo origen vía proxy → **sin CORS**; CSRF mitigado por `SameSite=Lax`.
- Silent-refresh al arrancar restaura la sesión sin token en JS.

## Next Steps
- [ ] Validación manual con los 2 servidores (uvicorn + vite) — checklist en el plan archivado.
- [ ] `/code-review` de los cambios.
- [ ] PR (incluye el cabo suelto de Fase 1 backend, aún sin PR).
- [ ] Fast-follow: pantallas forgot/reset/change-password (cliente ya listo).
