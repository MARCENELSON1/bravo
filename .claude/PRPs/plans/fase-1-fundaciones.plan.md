# Plan: Fase 1 — Fundaciones + Sistema de Identidad/Login completo

> **Convención de idioma (vinculante):** todo el **código backend en inglés** (clases, funciones, variables, **endpoints**, tablas/columnas de DB, comentarios). La **UX en español** (contenido de emails, textos al usuario). Errores de API: `code` en inglés + `message` en español. Glosario ES→EN en `CLAUDE.md`. *La narrativa de este plan está en español; los identificadores son los reales (inglés).*

## Summary
Construir el esqueleto del backend de BRAVO con **Clean Architecture + Ports & Adapters + DI por contenedor**, **Postgres multi-tenant (filtro `tenant_id` + RLS)**, y un **sistema de login completo y seguro** (login con JWT access+refresh, hash de contraseñas, cambio/recuperación de contraseña por SMTP, verificación de email, invitaciones por tenant, RBAC, rate-limiting/lockout y audit). Es el cimiento del que dependen las 8 fases restantes. Toda pieza externa (DB, JWT, hashing, email) vive detrás de un **port** para ser intercambiable sin reconstrucción.

## User Story
Como **equipo de desarrollo / dueño de un local**, quiero **una base con arquitectura limpia, aislamiento multi-tenant y un login completo y seguro**, para **agregar cada módulo (orders, payments, invoicing…) protegido por usuarios/roles reales y sin retrabajo de la base**.

## Problem → Solution
**Hoy:** solo existe el frontend (Vite/React); no hay backend, ni multi-tenant, ni auth. → **Después:** backend FastAPI con capas, contenedor DI, Postgres con RLS por tenant, migraciones Alembic, y un subsistema de identidad completo, con tests (80%+ en dominio/casos de uso) y validación verde.

## Metadata
- **Complexity**: XL (Fundaciones + subsistema de identidad). Implementado por milestones (M0–M6).
- **Source PRD**: `.claude/PRPs/prds/bravo-cerebro-del-local.prd.md`
- **PRD Phase**: Fase 1 — Fundaciones + Identidad
- **Estimated Files**: ~45–55 archivos nuevos (backend completo inicial)

---

## UX Design

### Before / After
**Interno/fundacional** — sin UX visual nueva salvo endpoints de auth (consumidos por el frontend en fases siguientes). Los "touchpoints" son endpoints HTTP, no pantallas. **Contenido de emails en español** (UX).

### Interaction Changes (endpoints expuestos — paths en inglés)
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| `POST /api/v1/auth/login` | no existe | email+password → access+refresh JWT | OAuth2 password flow |
| `POST /api/v1/auth/refresh` | no existe | refresh token → nuevo par (rotación) | revoca el anterior |
| `POST /api/v1/auth/logout` | no existe | revoca refresh token | logout real (server-side) |
| `POST /api/v1/auth/change-password` | no existe | actual→nueva (logueado) | requiere access token |
| `POST /api/v1/auth/forgot-password` | no existe | email → manda link por SMTP | respuesta neutra (anti-enumeración) |
| `POST /api/v1/auth/reset-password` | no existe | reset token + nueva password | token un-solo-uso, hasheado, TTL corto |
| `POST /api/v1/auth/verify-email` | no existe | token → marca email verificado | link enviado al registrar |
| `POST /api/v1/tenants/onboarding` | no existe | crea Tenant + User OWNER | manda verificación |
| `POST /api/v1/users/invite` | no existe | OWNER invita staff a su tenant | RBAC: OWNER/MANAGER |
| `POST /api/v1/users/accept-invitation` | no existe | invitation token + password → activa | un-solo-uso |
| `GET /api/v1/ping` | no existe | devuelve `tenant_id` del token | demo de aislamiento |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 (crítico) | `docs/architecture/backend-clean-architecture.md` | all | **Fuente de TODOS los patrones**: capas, ports, repos, contenedor DI, RLS, multi-tenant, errores, testing, convenciones. (Snippets ilustrativos en español → traducir identificadores al inglés por glosario) |
| P0 (crítico) | `CLAUDE.md` | all | Reglas vinculantes, "Prohibido", y **convención de idioma + glosario ES→EN** |
| P1 (importante) | `.claude/PRPs/prds/bravo-cerebro-del-local.prd.md` | Technical Approach + Decisions Log | Decisiones que enmarcan la Fase 1 (RLS, RBAC, idioma) |
| P2 (referencia) | `components.json`, `package.json` | all | Contexto del frontend existente (no se toca en Fase 1) |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| FastAPI | fastapi.tiangolo.com | App factory, routers, `Depends`, `OAuth2PasswordBearer` para el login |
| SQLAlchemy 2.0 async | docs.sqlalchemy.org (async) | `create_async_engine` + `async_sessionmaker`; driver `postgresql+asyncpg`; `DeclarativeBase`; `expire_on_commit=False` |
| dependency-injector | python-dependency-injector.ets-labs.org | `DeclarativeContainer`, `providers.Factory/Singleton`, `@inject`+`Provide`, `wiring_config` |
| Alembic async | alembic.sqlalchemy.org | `env.py` async con `connection.run_sync(...)` |
| Postgres RLS | postgresql.org/docs (Row Security) | `ENABLE`+`FORCE ROW LEVEL SECURITY`; `POLICY ... USING (tenant_id = current_setting('app.tenant_id')::uuid)`; `SET LOCAL` por transacción |
| pydantic-settings | docs.pydantic.dev | `BaseSettings` + `SettingsConfigDict(env_file=".env")` |
| pyjwt | pyjwt.readthedocs.io | `jwt.encode/decode`; manejar `ExpiredSignatureError`/`InvalidTokenError` |
| password hashing | argon2-cffi / passlib | `argon2-cffi` recomendado; **GOTCHA** compat passlib+bcrypt≥4.1 |
| aiosmtplib | aiosmtplib.readthedocs.io | Envío SMTP async con STARTTLS; credenciales por settings |

```
KEY_INSIGHT: RLS sólo aplica si la sesión NO es superuser/owner; el owner lo bypassa salvo FORCE.
APPLIES_TO: migración inicial + rol de DB de la app.
GOTCHA: usar un rol de aplicación dedicado (no superuser) y `ALTER TABLE ... FORCE ROW LEVEL SECURITY`; `SET LOCAL app.tenant_id` debe correr dentro de una transacción por request.

KEY_INSIGHT: passlib 1.7.4 + bcrypt>=4.1 emite error al leer la versión de bcrypt.
APPLIES_TO: adapter de hashing (PasswordHasher).
GOTCHA: usar `argon2-cffi` (recomendado, sin límite de 72 bytes) o pinear `bcrypt==4.0.1`.

KEY_INSIGHT: el refresh token debe poder revocarse (logout real).
APPLIES_TO: tabla refresh_tokens + casos de uso RefreshToken/Logout.
GOTCHA: guardar sólo el HASH del refresh token en DB, con rotación (cada refresh invalida el anterior). Igual para reset/verification/invitation tokens: hash + un-solo-uso + TTL.

KEY_INSIGHT: anti-enumeración de usuarios.
APPLIES_TO: endpoint POST /auth/forgot-password.
GOTCHA: responder SIEMPRE 200 con mensaje neutro (en español), exista o no el email.
```

---

## Patterns to Mirror

Patrones canónicos de la guía de arquitectura. Seguir EXACTO (con **identificadores en inglés**).

### NAMING_CONVENTION (código en inglés, UX en español)
// SOURCE: docs/architecture/backend-clean-architecture.md:361 + CLAUDE.md (glosario)
Código en inglés (`User`, `Tenant`, `Role`, `Invitation`, `Authenticate`). UX/emails en español. Tres cosas distintas, nunca confundir: **Entidad de dominio** (`User`) / **Modelo ORM** (`UserORM`) / **Schema Pydantic** (`UserResponse`), con **mappers** explícitos.

### DOMAIN_ENTITY (puro, sin frameworks)
// SOURCE: docs/architecture/backend-clean-architecture.md:100-129
`@dataclass` con reglas de negocio en métodos; sin imports de SQLAlchemy/FastAPI. Ej.: `User` con `can_login()`; la verificación de password delega al port `PasswordHasher` (el dominio no implementa crypto).

### REPOSITORY_PORT (en el dominio)
// SOURCE: docs/architecture/backend-clean-architecture.md:133-143
`class UserRepository(ABC)` con métodos async (`get_by_email`, `save`) — el dominio define QUÉ necesita.

### SERVICE_PORT (servicios externos como interfaces del dominio)
// SOURCE: docs/architecture/backend-clean-architecture.md:147-155
`PasswordHasher`, `TokenService`, `EmailSender` como ABC en el dominio; sus adapters en `infrastructure`.

### USE_CASE (constructor DI, depende de ports)
// SOURCE: docs/architecture/backend-clean-architecture.md:163-184
`class Authenticate: def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService)`. El caso de uso no sabe qué implementación corre.

### REPOSITORY_IMPL (filtra por tenant SIEMPRE)
// SOURCE: docs/architecture/backend-clean-architecture.md:194-216
`SqlAlchemyUserRepository` usa `session_factory` + mapper; toda query incluye `tenant_id`.

### ROUTER_FINO (sin lógica; @inject + Provide)
// SOURCE: docs/architecture/backend-clean-architecture.md:253-272
Router traduce HTTP⇄DTO y delega en el caso de uso vía `Depends(Provide[Container.authenticate])`.

### DI_CONTAINER
// SOURCE: docs/architecture/backend-clean-architecture.md:278-304
`DeclarativeContainer` con `config`, `db`, repos (Factory), servicios (Singleton), casos de uso (Factory); `wiring_config = WiringConfiguration(packages=["app.presentation"])`.

### MULTI_TENANT (ContextVar + RLS)
// SOURCE: docs/architecture/backend-clean-architecture.md:320-334
`tenant_id` del JWT → `ContextVar` en dependency; repos filtran por tenant; RLS con `current_setting('app.tenant_id')` seteado por sesión.

### ERROR_HANDLING (excepciones de dominio → HTTP en presentation)
// SOURCE: docs/architecture/backend-clean-architecture.md:338-342
El dominio lanza `InvalidCredentials`, `InvalidToken`, etc.; `presentation/errors.py` las mapea a 401/404/409/422 con `{code, message}` (code EN, message ES). Nunca `HTTPException` desde dominio/caso de uso.

### TEST_OVERRIDE (fakes via contenedor)
// SOURCE: docs/architecture/backend-clean-architecture.md:312-316
`container.user_repository.override(providers.Factory(FakeUserRepository))` para tests unit de casos de uso sin DB.

---

## Files to Change

> Todo es **CREATE** (el backend no existe). Carpeta raíz nueva: `backend/`. **Paths e identificadores en inglés.**

| Área | Archivos (representativos) | Acción |
|---|---|---|
| Tooling | `backend/pyproject.toml`, `backend/.env.example`, `backend/README.md` | CREATE |
| Config | `app/config.py` (`Settings`) | CREATE |
| DB infra | `app/infrastructure/persistence/database.py`, `models.py`, `mappers.py` | CREATE |
| Domain | `app/domain/tenant/{entities,exceptions,repository}.py`, `app/domain/user/{entities,value_objects,exceptions,repository}.py`, `app/domain/identity/ports.py` (`PasswordHasher`, `TokenService`, `EmailSender`, token repos) | CREATE |
| Application | `app/application/identity/{authenticate,refresh_token,logout,change_password,request_password_reset,reset_password,verify_email,onboard_tenant,invite_user,accept_invitation,dtos}.py` | CREATE |
| Infra · security | `app/infrastructure/security/{hasher.py (Argon2Hasher), token_service.py (JwtTokenService)}` | CREATE |
| Infra · email | `app/infrastructure/email/smtp_sender.py` (`SmtpEmailSender`), `templates/` (ES) | CREATE |
| Infra · repos | `app/infrastructure/persistence/{tenant_repo,user_repo,refresh_token_repo,reset_token_repo,verification_token_repo,invitation_repo,audit_repo}.py` | CREATE |
| Presentation | `app/presentation/api/v1/{auth,tenants,users,ping}.py`, `app/presentation/schemas/*.py`, `app/presentation/deps.py`, `app/presentation/errors.py`, `app/presentation/rbac.py` | CREATE |
| Wiring | `app/container.py`, `app/main.py` | CREATE |
| Migraciones | `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_initial.py` | CREATE |
| Tests | `backend/tests/unit/...`, `backend/tests/integration/...`, `backend/tests/conftest.py`, `backend/tests/fakes/*.py` | CREATE |

## NOT Building (fuera de alcance de la Fase 1)
- Dominio de orders/payments/invoicing/timeclock/inventory/reservations/copilot (fases 2–9).
- Frontend de login (se hace cuando el front consuma estos endpoints; Fase 1 es backend).
- 2FA/MFA, login social/OAuth externo, SSO (futuro).
- Gestión avanzada de usuarios desde UI — sólo lo necesario para onboarding/invitaciones.
- Rate-limiting distribuido con Redis (v1: contador en DB + lockout; Redis como evolución).
- Plantillas de email ricas/branding (v1: plantillas simples en español).

---

## Step-by-Step Tasks (por milestones)

### M0 · Bootstrap del proyecto

#### Task 1: Inicializar backend con Poetry y estructura de capas
- **ACTION**: Crear `backend/` con Poetry y la estructura `app/{domain,application,infrastructure,presentation}` + `tests/` + `alembic/`.
- **IMPLEMENT**: `pyproject.toml` con deps: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic`, `pydantic-settings`, `dependency-injector`, `pyjwt`, `argon2-cffi`, `aiosmtplib`, `python-multipart`. Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`, `pytest-cov`.
- **MIRROR**: estructura de carpetas — SOURCE arch doc:43-92.
- **GOTCHA**: `python = "^3.12"`. Nombres de paquetes/módulos en inglés.
- **VALIDATE**: `cd backend && poetry install`; `poetry run python -c "import app"`.

#### Task 2: Config con pydantic-settings + .env.example
- **ACTION**: `app/config.py` con `Settings(BaseSettings)`.
- **IMPLEMENT**: campos `env`, `database_url`, `jwt_secret`, `jwt_alg="HS256"`, `access_token_ttl_min`, `refresh_token_ttl_days`, `reset_token_ttl_min`, `verification_token_ttl_hours`, `smtp_host/port/user/password/from_email/use_tls`, `app_base_url`, `max_login_attempts`, `lockout_minutes`.
- **MIRROR**: `config.py` — SOURCE arch doc:85, 289.
- **IMPORTS**: `from pydantic_settings import BaseSettings, SettingsConfigDict`.
- **GOTCHA**: nunca loggear secretos; `.env` en `.gitignore`; commitear sólo `.env.example`.
- **VALIDATE**: test que instancia `Settings` con env de prueba.

### M1 · Persistencia + Multi-tenant + RLS

#### Task 3: Database async (engine + session factory + SET LOCAL tenant)
- **ACTION**: `app/infrastructure/persistence/database.py` con clase `Database`.
- **IMPLEMENT**: `create_async_engine(url)`, `async_sessionmaker(expire_on_commit=False)`; método `session()` que abre transacción y ejecuta `SET LOCAL app.tenant_id = :tid` cuando hay tenant en el `ContextVar`.
- **MIRROR**: `Database` provider — SOURCE arch doc:282-293, 320-334.
- **IMPORTS**: `from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession`; `from sqlalchemy import text`.
- **GOTCHA**: `SET LOCAL` sólo dura la transacción → `async with session.begin():`. Driver `postgresql+asyncpg://`.
- **VALIDATE**: integración: `SELECT current_setting('app.tenant_id', true)` devuelve el tenant seteado.

#### Task 4: Modelos ORM + mappers + Base
- **ACTION**: `models.py` (`TenantORM`, `UserORM`, `RefreshTokenORM`, `PasswordResetTokenORM`, `EmailVerificationTokenORM`, `InvitationORM`, `AuthAuditORM`) y `mappers.py`.
- **IMPLEMENT**: `DeclarativeBase`; PK `uuid`; columna `tenant_id` (FK) en tablas tenant-scoped; índice único `(tenant_id, email)` en users; las token tables guardan **hash** (no el valor), `expires_at`, `used`.
- **MIRROR**: separación entidad/ORM + mappers — SOURCE arch doc:67-72, 362-366.
- **GOTCHA**: la tabla `tenants` NO se filtra por `tenant_id` (es el propio tenant); su acceso se restringe por la lógica de onboarding/login.
- **VALIDATE**: `mypy` ok; test de mapper ORM⇄entidad ida y vuelta.

#### Task 5: Migración inicial Alembic (async) + RLS
- **ACTION**: `alembic/env.py` async + `versions/0001_initial.py`.
- **IMPLEMENT**: crear tablas; en tenant-scoped: `ENABLE` + `FORCE ROW LEVEL SECURITY` y `CREATE POLICY tenant_isolation USING (tenant_id = current_setting('app.tenant_id')::uuid)`. Crear rol de aplicación no-superuser.
- **MIRROR**: RLS — SOURCE arch doc:320-334.
- **IMPORTS**: en `env.py`, patrón `connection.run_sync(...)` async.
- **GOTCHA**: owner/superuser bypassa RLS salvo `FORCE`; la app se conecta con el rol no-superuser.
- **VALIDATE**: `poetry run alembic upgrade head` sobre DB de test; verificar `pg_policies`.

### M2 · Dominio de identidad

#### Task 6: Entidades, value objects, excepciones y ports
- **ACTION**: dominio `tenant/` y `user/` + `identity/ports.py`.
- **IMPLEMENT**: `Role(Enum)` = OWNER/MANAGER/WAITER/KITCHEN/CASHIER; `Email` VO (validación de formato); `User` (`email`, `password_hash`, `role`, `email_verified`, `active`, `failed_attempts`, `locked_until`) con métodos `register_failed_attempt`, `reset_attempts`, `can_login`. Ports: `UserRepository`, `TenantRepository`, `RefreshTokenRepository`, `ResetTokenRepository`, `VerificationTokenRepository`, `InvitationRepository`, `AuditRepository`, `PasswordHasher`, `TokenService`, `EmailSender`. Excepciones: `InvalidCredentials`, `UserLocked`, `EmailNotVerified`, `InvalidToken`, `ExpiredToken`, `TenantAlreadyExists`, `InvalidInvitation`.
- **MIRROR**: entidad/port — SOURCE arch doc:100-155.
- **GOTCHA**: el dominio NO importa hashlib/jwt/anthropic; hashing/JWT vía ports.
- **VALIDATE**: unit puro de invariantes (`can_login` con lockout, `Email` inválido lanza).

### M3 · Casos de uso (application)

#### Task 7: Casos de uso de auth core
- **ACTION**: `Authenticate`, `RefreshToken`, `Logout`, `ChangePassword`.
- **IMPLEMENT**: `Authenticate`: buscar por `(tenant, email)`; si locked → `UserLocked`; verificar hash vía `PasswordHasher`; si falla, `register_failed_attempt` + audit; si ok, emitir access+refresh (guardar **hash** del refresh) + `reset_attempts`. `RefreshToken`: validar refresh contra hash en DB, **rotar** (revocar viejo, emitir nuevo). `Logout`: revocar refresh. `ChangePassword`: verificar actual, setear nueva, revocar refresh tokens.
- **MIRROR**: caso de uso con ports por constructor — SOURCE arch doc:163-184.
- **GOTCHA**: respuestas neutras; mismo `InvalidCredentials` para "password incorrecta" y "usuario inexistente".
- **VALIDATE**: unit con fakes (override del contenedor): happy path + lockout + refresh rotado.

#### Task 8: Casos de uso de recuperación/verificación/invitaciones
- **ACTION**: `RequestPasswordReset`, `ResetPassword`, `VerifyEmail`, `OnboardTenant`, `InviteUser`, `AcceptInvitation`.
- **IMPLEMENT**: tokens con `secrets.token_urlsafe`, guardados **hasheados** con TTL y `used=false`; `EmailSender` manda el link (`app_base_url` + token) con **contenido en español**. `RequestPasswordReset` responde neutro siempre. `OnboardTenant` crea Tenant + User OWNER y manda verificación. `InviteUser` (RBAC OWNER/MANAGER) crea user inactivo + email de invitación; `AcceptInvitation` setea password y activa.
- **MIRROR**: ports de servicio externo (email) — SOURCE arch doc:147-155.
- **GOTCHA**: tokens **un-solo-uso** (marcar `used`), validar expiración, comparar por hash. Sin datos sensibles en el token.
- **VALIDATE**: unit con `FakeEmailSender` capturando el último envío; verificar un-solo-uso y expiración.

### M4 · Infraestructura (adapters)

#### Task 9: Adapters de seguridad y email + repos
- **ACTION**: `Argon2Hasher`(PasswordHasher), `JwtTokenService`(TokenService), `SmtpEmailSender`(EmailSender), y los repos SQLAlchemy.
- **IMPLEMENT**: hashing con argon2-cffi; JWT con pyjwt (claims: `sub`, `tenant_id`, `role`, `exp`, `type`); SMTP con aiosmtplib + STARTTLS; repos que mapean ORM⇄entidad y filtran por `tenant_id`.
- **MIRROR**: repo impl — SOURCE arch doc:194-216.
- **GOTCHA**: pyjwt → capturar `ExpiredSignatureError`/`InvalidTokenError` → `ExpiredToken`/`InvalidToken`. SMTP: credenciales por settings, jamás en logs.
- **VALIDATE**: integración: hash+verify round-trip; encode+decode JWT; repos contra DB de test.

### M5 · Presentación + Wiring

#### Task 10: deps, RBAC, errors, routers, schemas
- **ACTION**: `deps.py` (`current_user`/`current_tenant` desde access token → ContextVar), `rbac.py` (`require_roles(*roles)`), `errors.py`, routers `auth/tenants/users/ping`, schemas Pydantic.
- **IMPLEMENT**: `OAuth2PasswordBearer` para el login; cada endpoint delega en su caso de uso vía `Provide[...]`; `GET /ping` devuelve el `tenant_id` del token. Respuestas de error `{code, message}` (code EN, message ES).
- **MIRROR**: router fino + errores — SOURCE arch doc:253-272, 338-342.
- **GOTCHA**: routers SIN lógica; mapear excepciones de dominio a HTTP en `errors.py`.
- **VALIDATE**: e2e: login→/ping correcto; token de otro tenant NO ve datos del primero; rol insuficiente → 403.

#### Task 11: Container DI + main.py
- **ACTION**: `container.py` (cablea config, db, repos, hasher, tokens, email, casos de uso) y `main.py` (app factory, lifespan, routers, error handlers, wiring).
- **IMPLEMENT**: `wiring_config = WiringConfiguration(packages=["app.presentation"])`; repos/casos como `Factory`, servicios como `Singleton`; `lifespan` dispone el engine.
- **MIRROR**: container — SOURCE arch doc:278-304.
- **GOTCHA**: wiring al arrancar; `Provide` en `Depends`; Factory para per-request.
- **VALIDATE**: `poetry run uvicorn app.main:app` levanta; `/docs` muestra los endpoints.

### M6 · Tests + Validación

#### Task 12: Suite de tests (unit + integration + e2e) y cobertura
- **ACTION**: `conftest.py`, fakes de todos los ports, tests por capa.
- **IMPLEMENT**: unit (dominio + casos de uso con override del contenedor, sin DB); integration (repos + RLS de aislamiento entre 2 tenants); e2e (flujos completos con `httpx.AsyncClient`).
- **MIRROR**: testing — SOURCE arch doc:346-355, 312-316.
- **GOTCHA**: el test de RLS se conecta con el rol de app (no superuser).
- **VALIDATE**: ver "Validation Commands"; cobertura ≥80% en `domain/` y `application/`.

---

## Testing Strategy

### Unit Tests (sin DB, con fakes)
| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| `User.can_login` | user con `locked_until` futuro | `UserLocked` | sí (lockout) |
| `Authenticate` happy | email+password correctos | access+refresh emitidos | no |
| `Authenticate` fail | password incorrecta | `InvalidCredentials` + attempt++ | sí |
| `RefreshToken` | refresh válido | par nuevo, viejo revocado | sí (rotación) |
| `ResetPassword` | token expirado | `ExpiredToken` | sí |
| `RequestPasswordReset` | email inexistente | 200 neutro, sin email real | sí (anti-enumeración) |
| `Email` VO | string sin `@` | error de validación | sí |

### Integration / E2E
- RLS: tenant A no ve users de tenant B (query devuelve vacío).
- Flujo: onboarding → verify-email → login → /ping → change-password → logout → refresh revocado falla.
- Invitación: OWNER invita → accept → login del invitado con su rol.

### Edge Cases Checklist
- [ ] Email duplicado dentro del mismo tenant (único `(tenant_id, email)`)
- [ ] reset/verification/invitation token reusado (un-solo-uso)
- [ ] Token expirado
- [ ] Lockout tras N intentos
- [ ] Refresh token revocado/rotado
- [ ] Acceso cross-tenant denegado (RLS)
- [ ] Rol insuficiente (403)
- [ ] SMTP caído (no filtrar info; manejar error)

---

## Validation Commands

### Static Analysis
```bash
cd backend && poetry run ruff check . && poetry run mypy app
```
EXPECT: cero errores de lint y de tipos.

### Unit + Coverage
```bash
cd backend && poetry run pytest tests/unit -q --cov=app/domain --cov=app/application --cov-report=term-missing
```
EXPECT: todos verdes; cobertura ≥80% en domain/application.

### Integration / E2E
```bash
cd backend && poetry run pytest tests/integration -q
```
EXPECT: RLS aísla; flujos de auth completos pasan.

### Database / Migraciones
```bash
cd backend && poetry run alembic upgrade head
```
EXPECT: esquema creado, políticas RLS activas (verificar en `pg_policies`).

### Dev server
```bash
cd backend && poetry run uvicorn app.main:app --reload
```
EXPECT: `/docs` lista los endpoints; `GET /api/v1/ping` con token válido devuelve el tenant.

### Manual Validation
- [ ] Crear 2 tenants; con el token de uno NO se ven datos del otro.
- [ ] forgot-password: llega el email en español (MailHog/local), el link funciona una sola vez.

---

## Acceptance Criteria
- [ ] Esqueleto Clean Arch con las 4 capas y dependencias hacia adentro.
- [ ] Postgres multi-tenant con RLS verificada (aislamiento entre tenants).
- [ ] Contenedor DI cableado + test de override con fakes.
- [ ] Sistema de login completo: login, access+refresh (rotación/revocación), change/reset (SMTP) + verify-email, invitaciones, RBAC, rate-limit/lockout, audit.
- [ ] Migraciones Alembic aplicables; `.env.example` documentado.
- [ ] Validaciones (ruff, mypy, pytest, alembic) en verde; cobertura ≥80% en domain/application.
- [ ] **Idioma:** todo el código/endpoints/DB en inglés; emails y mensajes de error al usuario en español.

## Completion Checklist
- [ ] Código respeta los patrones de la guía (ports, repos, container, mappers).
- [ ] Excepciones de dominio mapeadas a HTTP en `presentation/errors.py` (no en routers).
- [ ] Ninguna query sin filtro de `tenant_id`.
- [ ] Servicios externos (hash, JWT, email) detrás de su port + provider en el container.
- [ ] Tokens (refresh/reset/verification/invitation) hasheados, un-solo-uso, con TTL.
- [ ] Sin secretos hardcodeados (todo por settings/`.env`).
- [ ] Identificadores en inglés; UX (emails/errores visibles) en español.
- [ ] Autocontenido — sin necesidad de buscar en el código durante la implementación.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| RLS mal configurada (bypass por owner/superuser) | M | Alto (fuga entre tenants) | `FORCE ROW LEVEL SECURITY` + rol app no-superuser + test de aislamiento obligatorio |
| Fase 1 XL: demasiado alcance en una pasada | H | Medio (retraso) | Implementar por milestones M0–M6; cada uno con validación propia |
| Seguridad de tokens (reset/refresh) mal hecha | M | Alto | Hash en DB + un-solo-uso + TTL + rotación; pasar `security-reviewer` antes de mergear |
| Deliverabilidad SMTP en dev | M | Bajo | MailHog/local para dev; `EmailSender` port permite cambiar a SES/SendGrid sin tocar lógica |

## Notes
- **Convención de idioma:** código/endpoints/DB en inglés; UX (emails, textos, `message` de error) en español. Glosario ES→EN en `CLAUDE.md`.
- **Confidence Score**: 7/10 para single-pass — el alcance XL (identidad completa) baja la confianza; mitigado por milestones y patrones ya documentados. Recomendado pasar `security-reviewer` sobre los casos de uso de auth antes de cerrar la fase.
- La guía `docs/architecture/backend-clean-architecture.md` es la referencia canónica del PATRÓN; sus snippets están en español (ilustrativos) — traducir identificadores al inglés por glosario.
