# Plan: Identidad Wellnod — portar la identidad visual de `origin/tita`

## Summary
Adoptar la identidad visual de la rama `origin/tita` (commit `2497ebc`: glassmorphism, marca Wellnod, paleta verde oklch, Inter) portándola **selectivamente** sobre `main` — sin mergear la rama. Se reemplaza la maqueta mock de tita por datos reales: nav híbrida con gating por rol, saludo con nombre real (columna nueva `users.name`), y el dashboard rediseñado cableado a los endpoints existentes + un endpoint nuevo de serie diaria.

## User Story
Como dueño/encargado de un local, quiero una app con identidad de marca propia (Wellnod) y un dashboard que me hable ("Buen día, Juan") con mis números reales, para sentir un producto pulido sin perder ninguna capacidad operativa actual.

## Problem → Solution
Hoy la app se llama NÚCLEO con estética de consola genérica; `origin/tita` propone la identidad Wellnod pero es una maqueta con datos falsos que además borra navegación operativa y fuerza dark. → Portamos el lenguaje visual de tita sobre la funcionalidad real de `main`: todo sigue andando, pero se ve Wellnod.

## Metadata
- **Complexity**: Large (2 tandas, ~28 archivos)
- **Source PRD**: N/A (decisiones cerradas en conversación 2026-07-03; memoria `plan-identidad-wellnod.md`)
- **PRD Phase**: standalone
- **Estimated Files**: ~16 frontend, ~12 backend + 1 migración

## Decisiones cerradas (NO re-preguntar)
1. **"Wellnod" es el nombre definitivo** visible al usuario (sidebar, login, título, emails).
2. **Tokens de tema: los de tita completos** (pisan la paleta Verdes+Grises de `main`; tita trae variante clara Y oscura).
3. **Nav híbrida**: 6 ítems planos de tita arriba + grupos "Operación" y "Gestión" debajo. **Gating por rol SIEMPRE** (lo más importante para el usuario).
4. **Tema según el SO**: `defaultTheme="system"` + conservar `ThemeToggle` y `ClockStatus`. Únicos cambios deliberados vs tita.

## Prerrequisito de secuencia
⚠️ **La Tanda C de Finanzas (migración `0015_advisor_diagnostics`) debe estar commiteada/mergeada a `main` ANTES de arrancar.** La migración de este plan es `0016_user_name` con `down_revision = "0015_advisor_diagnostics"`. Si Tanda C no está en `main`, la cadena de Alembic se rompe. (Las tandas D/E/F de Finanzas corren su numeración a 0017/0018/0019.)

Rama de trabajo: `feat/identidad-wellnod` desde `main` actualizado.

---

## UX Design

### Before (main hoy)
```
┌────────────┬──────────────────────────────────┐
│ ▪ NÚCLEO   │ [≡]              (reloj)(tema)   │  sidebar sólida pegada al borde
│ RESUMEN    ├──────────────────────────────────┤  6 grupos / ~17 ítems
│  Dashboard │  Resumen                         │  dashboard: 5 KPIs TextureCard
│  Finanzas  │  [KPI][KPI][KPI]                 │  + accesos rápidos
│  ...       │  [KPI][KPI]                      │
│ OPERACIÓN  │  Accesos rápidos [..][..][..]    │
│  ...×6grp  │                                  │
│ rol/tenant │                                  │
└────────────┴──────────────────────────────────┘
```

### After (Wellnod)
```
╔═ fondo gradiente escénico (claro u oscuro según SO) ═╗
║ ╭─────────────╮  ╭─────────────────────────────────╮ ║
║ │ ⟡ Wellnod   │  │ Nombre del local  🕐 ☾/☀ (JM)  │ ║  paneles de vidrio flotantes
║ │  ⌂ Inicio   │  ├─────────────────────────────────┤ ║  (rounded-2xl + blur)
║ │  ↗ Finanzas │  │ Buen día, Juan      jue 3 jul   │ ║  avatar iniciales→logout
║ │  ◉ Clientes │  │ [KPI][KPI][KPI][KPI][KPI]       │ ║
║ │  ▢ Productos│  │ [Gráfico 7 días ▂▄▆█][Recos IA] │ ║  todo con DATOS REALES
║ │  ✦ IA Insig.│  │ [Medios de pago][Proyección]    │ ║
║ │  ≡ Reportes │  │                            (+)  │ ║  FAB → registrar egreso
║ │ OPERACIÓN   │  ╰─────────────────────────────────╯ ║
║ │  Mesas KDS..│                                      ║
║ │ GESTIÓN     │                                      ║
║ │  Asesor ... │                                      ║
║ ╰─────────────╯                                      ║
╚══════════════════════════════════════════════════════╝
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Marca | "NÚCLEO / El cerebro del local" | Isotipo hélice + "Wellnod" | sidebar + login + título |
| Topbar | reloj + toggle | nombre del local + reloj + toggle + avatar iniciales (hover→logout) | SIN campana, SIN "Plan Pro" |
| Logout | botón en footer sidebar | avatar en topbar | footer sidebar desaparece |
| Nav | 6 grupos | 6 ítems planos + grupos Operación/Gestión | mismos destinos, roles idénticos |
| Dashboard | "Resumen" 5 KPIs + shortcuts | "Buen día, {nombre}" + 5 KPIs + gráfico 7d + recos IA + pago mix + proyección + FAB | solo OWNER/MANAGER lo ven (RoleLanding redirige al resto) |
| Onboarding | sin nombre de persona | campo opcional "Tu nombre" | alimenta el saludo |
| Emails | "— El equipo de BRAVO" | "— El equipo de Wellnod" | templates backend |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `git show 2497ebc` (origin/tita) | todo el diff | fuente visual: wellnod-mark, app-shell glass, dashboard layout, index.css, auth bypass |
| P0 | `frontend/src/components/shell/app-shell.tsx` | all (123) | estructura actual a reescribir; conservar ClockStatus/ThemeToggle/drawer |
| P0 | `frontend/src/components/shell/nav-config.ts` | all (149) | ítems/roles/rutas actuales — la híbrida debe cubrir TODOS |
| P0 | `backend/app/presentation/api/v1/analytics.py` | all | patrón canónico de router GET con from/to/limit + RBAC + DI |
| P0 | `backend/app/infrastructure/persistence/analytics_repo.py` | 24-56, 149-161 | patrón read model SQL (tenant filter, rangos, group_by) |
| P1 | `frontend/src/auth/auth-provider.tsx` | all | boot refresh()→me(); acá se inyecta el bypass y la Session extendida |
| P1 | `backend/app/application/identity/onboard_tenant.py` | 52-70 | dónde se crea el User (agregar name) |
| P1 | `backend/app/infrastructure/persistence/mappers.py` | 112-138 | user_to_domain / user_to_orm (agregar name) |
| P1 | `backend/alembic/versions/0015_advisor_diagnostics.py` | all | patrón de migración (header/revision); la nuestra usa op.add_column |
| P1 | `frontend/src/features/finance/finance-page.tsx` | 90-178 | cómo se consumen overview.projection y diagnostics (reusar en dashboard) |
| P2 | `frontend/src/features/dashboard/dashboard-page.tsx` | all (129) | página actual a reemplazar; conservar patrón pending→"—" y AnimatedNumber |
| P2 | `backend/app/presentation/api/v1/ping.py` | all (19) | mini-router a espejar para /me |
| P2 | `frontend/src/api/analytics-api.test.ts` | all | patrón de test de API client |
| P2 | `backend/tests/integration/test_e2e_analytics.py` | 119-151, 215-225 | patrón integración GET + test RLS de aislamiento |

## External Documentation
| Topic | Source | Key Takeaway |
|---|---|---|
| — | — | No external research needed — todo usa patrones internos ya establecidos. `@fontsource-variable/inter` se usa igual que la geist ya instalada. |

---

## Patterns to Mirror

### ROUTER_GET_CON_RANGO (backend)
```python
# SOURCE: backend/app/presentation/api/v1/analytics.py:15-35
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/revenue", response_model=RevenueSummaryResponse)
@inject
async def get_revenue(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetRevenueSummary = Depends(Provide[Container.get_revenue_summary]),
) -> RevenueSummaryResponse:
    s = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return RevenueSummaryResponse(currency=s.currency, ...)  # mapeo explícito DTO→schema
```
Registrar el router nuevo en `backend/app/main.py` (import arriba + `app.include_router(x.router, prefix="/api/v1")`).

### USE_CASE_LECTURA + PORT (backend)
```python
# SOURCE: backend/app/application/analytics/use_cases.py:18-33 y read_models.py
class GetRevenueSummary:
    def __init__(self, read_model: RevenueReadModel, tenant_context: TenantContext) -> None: ...
    async def execute(self, *, tenant_id: str, since=None, until=None) -> RevenueSummary:
        self._tenant_context.set(tenant_id)
        return await self._read_model.summary(tenant_id, since=since, until=until)
# El port (ABC) y su dataclass DTO viven en app/application/analytics/read_models.py
```

### READ_MODEL_SQL (backend)
```python
# SOURCE: backend/app/infrastructure/persistence/analytics_repo.py:45-56
sales_stmt = select(
    func.coalesce(func.sum(SaleFactORM.line_amount), 0), ...
).where(SaleFactORM.tenant_id == tenant_id)          # filtro tenant SIEMPRE (además de RLS)
if since is not None:
    sales_stmt = sales_stmt.where(SaleFactORM.occurred_at >= since)
# clase: Sql<X>ReadModel(<PortABC>), __init__(session_factory), async with self._session_factory() as session
```

### WIRING_CONTAINER (backend)
```python
# SOURCE: backend/app/container.py:853-872
revenue_read_model = providers.Factory(SqlAlchemyRevenueReadModel, session_factory=db.provided.session)
get_revenue_summary = providers.Factory(GetRevenueSummary, read_model=revenue_read_model, tenant_context=tenant_context)
# Auto-wiring: wiring_config ya cubre app.presentation — no hay que registrar routers.
```

### API_CLIENT + HOOK (frontend)
```ts
// SOURCE: frontend/src/api/reports-api.ts + frontend/src/hooks/use-dashboard.ts
export class ReportsApi {
  constructor(private http: HttpClient) {}
  getDashboard(): Promise<DashboardSummaryDTO> {
    return this.http.request<DashboardSummaryDTO>("GET", "/reports/dashboard", { auth: true })
  }
}
export function useDashboard() {
  const { reportsApi } = useServices()
  return useQuery({ queryKey: ["dashboard-summary"], queryFn: () => reportsApi.getDashboard() })
}
// Registrar clientes nuevos en services-context.ts (interface) + services-provider.tsx (useMemo)
```

### TEST_API_CLIENT (frontend)
```ts
// SOURCE: frontend/src/api/analytics-api.test.ts
const request = vi.fn().mockResolvedValue({ currency: "ARS", sales_amount: 0 })
const api = new AnalyticsApi({ request } as unknown as HttpClient)
await api.revenue({ from: "2026-06-01T00:00:00.000Z" })
const [method, path, options] = request.mock.calls[0]
expect(method).toBe("GET"); expect(path).toContain("/analytics/revenue?"); expect(options).toMatchObject({ auth: true })
```

### TEST_INTEGRACION_GET + RLS (backend)
```python
# SOURCE: backend/tests/integration/test_e2e_analytics.py:119-151 y 215-225
h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
summary = (await http.get("/api/v1/analytics/revenue", headers=h)).json()
assert summary["sales_amount"] == 300000
# + test de aislamiento: segundo tenant debe ver 0 (copiar test_analytics_rls_isolation)
```

### MIGRACION (backend)
```python
# SOURCE: backend/alembic/versions/0015_advisor_diagnostics.py (header y estructura)
revision: str = "0016_user_name"
down_revision: str | None = "0015_advisor_diagnostics"
# ⚠️ Primera migración add_column del repo (las previas crean tablas con Base.metadata.create_all):
def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(120), nullable=True))
def downgrade() -> None:
    op.drop_column("users", "name")
```

### GLASS_TITA (frontend — lenguaje visual)
```tsx
// SOURCE: git show 2497ebc -- frontend/src/components/shell/app-shell.tsx (rama tita)
// Panel: rounded-2xl border border-white/10 bg-black/30 backdrop-blur-2xl
// Layout: <div className="relative flex h-svh gap-3 overflow-hidden p-3"> + fondo fixed -z-10
// Fondo tita (solo dark): bg-[radial-gradient(120%_120%_at_15%_10%,#9fb0aa_0%,#63736b_28%,#2c3833_58%,#101915_82%,#0a0f0c_100%)]
// Ítem nav activo: bg-sidebar-accent text-sidebar-accent-foreground shadow-sm (rounded-xl px-3 py-2.5)
// Card dashboard: rounded-2xl border border-white/10 bg-white/[0.045] shadow-xl shadow-black/20 backdrop-blur-2xl
```
**Adaptación modo claro (nuevo, no existe en tita):** cada clase hardcodeada dark se duplica con variante clara usando el prefijo `dark:`. Panel: `bg-white/60 border-black/10 dark:bg-black/30 dark:border-white/10`. Fondo claro: gradiente suave `#eef2f0 → #d8e2dd → #c4d2cb` (misma familia de verdes desaturados). Card: `bg-white/55 shadow-black/5 dark:bg-white/[0.045] dark:shadow-black/20`. Validar contraste a ojo en ambos temas.

---

## Files to Change

### Tanda Id-1 — Identidad base
| File | Action | Justification |
|---|---|---|
| `frontend/package.json` | UPDATE | dep `@fontsource-variable/inter` (^5.x, como geist) |
| `frontend/src/components/brand/wellnod-mark.tsx` | CREATE | copiar de tita: `git checkout origin/tita -- <path>` |
| `frontend/src/index.css` | REPLACE | `git checkout origin/tita -- frontend/src/index.css` (verificado: no pierde ningún token custom; suma `--font-display` + import inter) |
| `frontend/src/auth/auth-provider.tsx` | UPDATE | portar bypass `VITE_AUTH_BYPASS` de tita + hidratar Session extendida desde /me |
| `frontend/src/auth/session.ts` | UPDATE | Session += `name: string \| null`, `email: string`, `tenantName: string` |
| `frontend/src/api/types.ts` | UPDATE | `MeResponse` += `email`, `name`, `tenant_name` |
| `frontend/src/api/auth-api.ts` | UPDATE | `me()` pasa de `GET /ping` a `GET /me` |
| `frontend/src/api/auth-api.test.ts` | UPDATE | reflejar /me |
| `frontend/src/auth/guards.test.tsx` | UPDATE | fixtures de Session con campos nuevos |
| `frontend/src/components/shell/nav-config.ts` | REWRITE | nav híbrida (ver Task 8) |
| `frontend/src/components/shell/app-shell.tsx` | REWRITE | shell glass Wellnod (ver Task 9) |
| `frontend/src/components/auth/auth-layout.tsx` | UPDATE | marca Wellnod (líneas 27 y 44) |
| `frontend/index.html` | UPDATE | `<title>Wellnod</title>` |
| `frontend/src/features/identity/onboarding-page.tsx` | UPDATE | campo opcional "Tu nombre" → `owner_name` |
| `backend/alembic/versions/0016_user_name.py` | CREATE | `users.name` nullable |
| `backend/app/infrastructure/persistence/models.py` | UPDATE | `UserORM.name: Mapped[str \| None]` |
| `backend/app/domain/user/entities.py` | UPDATE | `User.name: str \| None = None` |
| `backend/app/infrastructure/persistence/mappers.py` | UPDATE | name en user_to_domain/user_to_orm |
| `backend/app/presentation/schemas/tenants.py` | UPDATE | `owner_name: str \| None` en OnboardingRequest |
| `backend/app/application/identity/dtos.py` | UPDATE | `owner_name` en OnboardTenantInput |
| `backend/app/application/identity/onboard_tenant.py` | UPDATE | pasa name al User |
| `backend/app/presentation/api/v1/tenants.py` | UPDATE | mapear owner_name al input |
| `backend/app/presentation/schemas/auth.py` | UPDATE | `MeResponse` nuevo (PingResponse queda igual) |
| `backend/app/application/identity/get_my_profile.py` | CREATE | use case GetMyProfile(users, tenants, tenant_context) |
| `backend/app/presentation/api/v1/me.py` | CREATE | `GET /me` (espejo de ping.py + DB) |
| `backend/app/container.py` | UPDATE | factory `get_my_profile` |
| `backend/app/main.py` | UPDATE | include me.router |
| `backend/app/infrastructure/email/templates.py` | UPDATE | BRAVO → Wellnod (6 strings) |
| `backend/tests/unit/test_get_my_profile.py` | CREATE | unit con fakes |
| `backend/tests/integration/test_e2e_auth.py` | UPDATE | asserts de /me + onboarding con nombre |

### Tanda Id-2 — Dashboard real
| File | Action | Justification |
|---|---|---|
| `backend/app/application/analytics/read_models.py` | UPDATE | port `RevenueDailyReadModel` + dataclass `RevenueDailyPoint` |
| `backend/app/application/analytics/use_cases.py` | UPDATE | `GetRevenueDaily` |
| `backend/app/infrastructure/persistence/analytics_repo.py` | UPDATE | `SqlAlchemyRevenueDailyReadModel` (group by día) |
| `backend/app/presentation/schemas/analytics.py` | UPDATE | `RevenueDailyPointResponse` |
| `backend/app/presentation/api/v1/analytics.py` | UPDATE | `GET /analytics/revenue/daily` |
| `backend/app/container.py` | UPDATE | factories daily |
| `backend/tests/integration/test_e2e_analytics.py` | UPDATE | test serie diaria + RLS |
| `frontend/src/api/types-analytics.ts` | UPDATE | `RevenueDailyPointDTO` |
| `frontend/src/api/analytics-api.ts` | UPDATE | `revenueDaily(query)` |
| `frontend/src/api/analytics-api.test.ts` | UPDATE | test del método nuevo |
| `frontend/src/hooks/use-analytics.ts` | UPDATE | `useRevenueDaily` |
| `frontend/src/features/dashboard/dashboard-page.tsx` | REWRITE | layout tita + datos reales |

## NOT Building
- ❌ Merge de `origin/tita` (se porta a mano).
- ❌ Dark forzado / borrar ThemeToggle o ClockStatus (decisión: según SO).
- ❌ Campana de notificaciones y tarjeta "Plan Pro" (no hay sistemas detrás; UI que miente es deuda).
- ❌ Renombrar claves de localStorage `nucleo_presence_device_token` / `nucleo:product-usage` (romperían presencia/uso sin migración de datos — quedan como identificadores internos).
- ❌ Renombrar identificadores internos backend: `bravo_app` (rol DB), `bravo_refresh` (cookie), `bravo-api` (issuer JWT), `FastAPI(title="BRAVO API")`, `no-reply@bravo.app` (dominio real). Solo se renombra lo visible al usuario.
- ❌ Captura de nombre en accept-invitation (iniciales del avatar caen al email; se puede sumar después).
- ❌ Consolidar Egresos/Comprobantes como pestañas dentro de Finanzas (tanda futura de pulido; por ahora viven en el grupo "Gestión").
- ❌ Foto real de fondo (queda el gradiente placeholder de tita + variante clara).
- ❌ Timezone local en la serie diaria (MVP trunca en UTC; se anota para revisión con feedback real).

---

## Step-by-Step Tasks

### — TANDA Id-1: IDENTIDAD BASE —

### Task 1: Dependencia Inter + assets de tita
- **ACTION**: Agregar `"@fontsource-variable/inter": "^5.2.8"` a `frontend/package.json` (junto a geist) y correr `npm install` en `frontend/`. Traer archivos copiables: `git checkout origin/tita -- frontend/src/components/brand/wellnod-mark.tsx frontend/src/index.css`.
- **GOTCHA**: NO traer de tita: `theme-provider.tsx` (forzaría dark), `nav-config.ts`, `app-shell.tsx`, `dashboard-page.tsx` (se reescriben acá). Verificado por diff: reemplazar `index.css` no pierde ningún token custom de main (sets idénticos, solo cambian valores).
- **VALIDATE**: `cd frontend && npm run build` → verde (si falta la dep de inter, el import del css rompe acá).

### Task 2: Bypass de auth para diseño (dev-only)
- **ACTION**: Portar a `frontend/src/auth/auth-provider.tsx` el bloque `AUTH_BYPASS` de tita (constante module-level + early-return en el boot + logout que re-hidrata la DEV_SESSION). Copiar la lógica del diff de tita, adaptando `DEV_SESSION` a la Session extendida de Task 6 (`name: "Dev"`, `email: "dev@wellnod.local"`, `tenantName: "Local de prueba"`).
- **MIRROR**: `git show 2497ebc -- frontend/src/auth/auth-provider.tsx`.
- **GOTCHA**: el guard es `import.meta.env.MODE === "development" && VITE_AUTH_BYPASS === "true"` — jamás activo en build de prod. Documentar la var en `.env.example` del frontend si existe.
- **VALIDATE**: `npm run build` verde; con `VITE_AUTH_BYPASS=true npm run dev` la app entra sin backend.

### Task 3: Migración `0016_user_name` + columna en capas
- **ACTION**: Crear `backend/alembic/versions/0016_user_name.py` (revision `0016_user_name`, down_revision `0015_advisor_diagnostics`) con `op.add_column("users", sa.Column("name", sa.String(120), nullable=True))` / `op.drop_column`. Agregar `name: Mapped[str | None] = mapped_column(String(120), nullable=True)` a `UserORM` (models.py:46-69), `name: str | None = None` a la entidad `User` (domain/user/entities.py), y mapear en `user_to_domain`/`user_to_orm` (mappers.py:112-138).
- **MIRROR**: patrón MIGRACION de arriba. Es el PRIMER `add_column` del repo (los anteriores usan `Base.metadata.create_all` para tablas nuevas): importar `sqlalchemy as sa`, no usar `_NEW_TABLES`. No hace falta RLS (la tabla `users` ya la tiene).
- **GOTCHA**: la entidad `User` es dataclass — `name` va con default `None` AL FINAL (los campos con default no pueden preceder a los sin default).
- **VALIDATE**: `cd backend && alembic upgrade head` sobre el dev DB → aplica 0016; `pytest -q` (unit) sin regresiones.

### Task 4: Onboarding captura el nombre (opcional)
- **ACTION**: `OnboardingRequest` (schemas/tenants.py) += `owner_name: str | None = Field(default=None, max_length=120)`. `OnboardTenantInput` (application/identity/dtos.py) += `owner_name: str | None = None`. En `onboard_tenant.py:52-70`, pasar `name=data.owner_name.strip() if data.owner_name else None` al crear el `User`. Mapear en el router `tenants.py`.
- **VALIDATE**: test de integración: onboarding con `owner_name` → luego /me lo devuelve (Task 5 lo cierra).

### Task 5: `GET /me` (backend)
- **ACTION**:
  1. `backend/app/application/identity/get_my_profile.py`: use case `GetMyProfile(users: UserRepository, tenants: TenantRepository, tenant_context: TenantContext)`; `execute(*, tenant_id, user_id)` → setea tenant_context, `users.get_by_id(tenant_id, user_id)` + `tenants.get_by_id(tenant_id)` (verificar firma exacta del tenant repo al implementar), retorna dataclass `MyProfile {user_id, tenant_id, role, email, name, tenant_name}`. Si user/tenant no existen → levantar el error de dominio que use el repo de auth (mirror de cómo authenticate maneja usuario inexistente).
  2. `schemas/auth.py`: `class MeResponse(BaseModel): tenant_id, user_id, role, email, name: str | None, tenant_name` (PingResponse NO se toca).
  3. `backend/app/presentation/api/v1/me.py`: router espejo de `ping.py` — `@router.get("/me", response_model=MeResponse)` con `identity: AccessClaims = Depends(current_identity)` + use case inyectado.
  4. `container.py`: `get_my_profile = providers.Factory(GetMyProfile, users=user_repository, tenants=tenant_repository, tenant_context=tenant_context)`.
  5. `main.py`: import + `app.include_router(me.router, prefix="/api/v1")`.
- **MIRROR**: ROUTER_GET_CON_RANGO (sin query params), USE_CASE_LECTURA, WIRING_CONTAINER; `ping.py` como esqueleto.
- **GOTCHA**: `/ping` queda intacto (health barato sin DB). `role` serializar como `str(identity.role)` igual que ping.
- **VALIDATE**: unit `backend/tests/unit/test_get_my_profile.py` con fakes (user con name y sin name); integración en `test_e2e_auth.py`: onboard con owner_name → login → `GET /api/v1/me` → asserts de `email`, `name`, `tenant_name`.

### Task 6: Frontend consume `/me` — Session con identidad
- **ACTION**: `types.ts`: `MeResponse` += `email: string`, `name: string | null`, `tenant_name: string`. `auth-api.ts`: `me()` pasa a `GET /me`. `session.ts`: `Session` += `email: string`, `name: string | null`, `tenantName: string`. `auth-provider.tsx`: en boot y post-login, `setSession({ userId, tenantId, role, email: me.email, name: me.name, tenantName: me.tenant_name })`.
- **GOTCHA**: `guards.test.tsx` y cualquier fixture que construya `Session` deben sumar los campos. El comentario de `session.ts` ("Hydrated from GET /ping") se actualiza.
- **VALIDATE**: `npm run test` (auth-api.test + guards.test verdes), `npm run build`.

### Task 7: Onboarding UI — campo "Tu nombre"
- **ACTION**: En `frontend/src/features/identity/onboarding-page.tsx` agregar `Field` opcional "Tu nombre" (mirror del Field de "Nombre del comercio", líneas 104-110) que mande `owner_name` en el payload de `authApi.onboard`. Actualizar el tipo del request en `auth-api.ts`/`types.ts` si el payload está tipado.
- **VALIDATE**: `npm run build` + smoke manual del form.

### Task 8: Nav híbrida (`nav-config.ts` REWRITE)
- **ACTION**: Exportar DOS estructuras (mantener interfaces `NavItem`/`NavGroup` actuales):
  ```
  NAV_ITEMS (plana, arriba):
    Inicio        /app            Home        [OWNER,MANAGER,WAITER,KITCHEN,BAR,CASHIER]  end:true
    Finanzas      /app/finanzas   LineChart   [OWNER,MANAGER]
    Clientes      /app/reservations Users     [OWNER,MANAGER,WAITER,CASHIER]
    Productos     /app/products   Package     [OWNER,MANAGER]
    IA Insights   /app/copilot    Lightbulb   [OWNER,MANAGER]
    Reportes      /app/analytics  FileText    [OWNER,MANAGER]
  NAV_GROUPS:
    "Operación":  Mesas /app/floor UtensilsCrossed [WAITER,CASHIER,MANAGER,OWNER] ·
                  Cocina /app/kds ChefHat [KITCHEN,MANAGER,OWNER] ·
                  Barra /app/bar Coffee [BAR,MANAGER,OWNER] ·
                  Caja /app/caja Calculator [CASHIER,MANAGER,OWNER] ·
                  Propinas /app/propinas Coins [CASHIER,MANAGER,OWNER] ·
                  Fichar /app/fichar QrCode [todos]
    "Gestión":    Asesor /app/advisor Sparkles · Egresos /app/expenses Receipt ·
                  Comprobantes /app/invoices FileText · Insumos /app/stock Boxes ·
                  Proveedores /app/suppliers Truck · Personal /app/staff Clock ·
                  Integraciones /app/integrations Plug · Equipo /app/invite Users
                  (todos [OWNER,MANAGER])
  ```
- **GOTCHA**: (1) Cobertura TOTAL: las 17 rutas de la nav actual deben seguir presentes — diff mental contra nav-config.ts actual antes de commitear. (2) "Reservas" desaparece como label: su ruta vive en "Clientes". (3) Icono `Users` se repite (Clientes y Equipo) — aceptable. (4) Roles copiados EXACTOS de la nav actual; no inventar.
- **VALIDATE**: `npm run build`; smoke manual con un usuario de cada rol (o revisar el filter con los 6 roles a mano).

### Task 9: AppShell glass Wellnod (REWRITE)
- **ACTION**: Reescribir `app-shell.tsx` combinando el layout de tita con la funcionalidad de main:
  - Layout root de tita: `relative flex h-svh gap-3 overflow-hidden p-3` + fondo `fixed inset-0 -z-10` con gradiente (variante clara y `dark:` la de tita — ver GLASS_TITA).
  - Sidebar panel glass: logo `<WellnodMark className="h-9 w-auto text-[#8a9d94]" /> + wordmark "Well|nod"` (copiar bloque de tita); nav = `NAV_ITEMS` filtrados por rol con estilo de ítem tita (rounded-xl), luego `NAV_GROUPS` con label uppercase chiquito (estilo actual de grupos, ítems estilo tita). SIN footer (ni rol/tenant ni Plan Pro).
  - Topbar dentro del panel de contenido: botón drawer móvil (conservar) + `{session.tenantName}` + `flex-1` + `<ClockStatus />` + `<ThemeToggle />` + avatar circular con iniciales (de `session.name` → dos primeras iniciales; fallback: primera letra de `session.email`) que en hover muestra `LogOut` y hace `void logout()` (patrón botón de tita), con `title={ROLE_LABELS[role]}`.
  - Drawer móvil: conservar el overlay actual, con el sidebar glass adentro (tita: `absolute inset-y-0 left-0 p-3`).
- **MIRROR**: GLASS_TITA + app-shell.tsx actual (funcionalidad).
- **GOTCHA**: (1) NO campana. (2) `ClockStatus`/`ThemeToggle` imports se conservan. (3) `main` interno mantiene `flex-1 overflow-auto` (el scroll queda DENTRO del panel). (4) Ítems inactivos legibles en claro: `text-sidebar-foreground/70` funciona en ambos si la sidebar usa tokens — preferir tokens sobre hardcodes donde tita usó `bg-black/30`.
- **VALIDATE**: `npm run build`; manual en claro y oscuro (desktop + drawer móvil).

### Task 10: Rename de marca visible
- **ACTION**: `auth-layout.tsx:27` → bloque marca Wellnod (WellnodMark + wordmark, mismo patrón que sidebar); `:44` → `© Wellnod`. `frontend/index.html:7` → `<title>Wellnod</title>`. Backend `infrastructure/email/templates.py`: las 6 strings BRAVO → Wellnod (`_SIGNATURE`, 2 subjects, 2 cuerpos, invitación).
- **GOTCHA**: grep `BRAVO` en `backend/tests/` — si algún test asserta subjects de email, actualizarlo. NO tocar: localStorage keys `nucleo*`, `bravo_app`/`bravo_refresh`/`bravo-api`/`no-reply@bravo.app`/`FastAPI(title=...)`.
- **VALIDATE**: `grep -ri "NÚCLEO" frontend/src` → solo las 2 localStorage keys; `cd backend && pytest -q`; `npm run build`.

### Task 11: Validación integral Tanda Id-1
- **ACTION**: correr TODO: `cd backend && pytest` (unit+integración, requiere Postgres), `cd frontend && npm run lint && npm run test && npm run build`. Manual: login → shell Wellnod en claro/oscuro → toggle → ClockStatus visible → navegar con cada rol (al menos OWNER y WAITER) → logout por avatar → onboarding nuevo con nombre → saludo pendiente (Tanda 2) pero /me responde.
- **VALIDATE**: checklist de Acceptance Criteria abajo. Commit + merge `--no-ff` a `main` (mensaje `feat(brand): identidad Wellnod — shell glass + nav híbrida + GET /me`).

### — TANDA Id-2: DASHBOARD REAL —

### Task 12: Serie diaria de facturación (backend)
- **ACTION**:
  1. `application/analytics/read_models.py`: `@dataclass(frozen=True) RevenueDailyPoint { day: date; sales_amount: int; orders_count: int }` + ABC `RevenueDailyReadModel.daily(tenant_id, *, since, until) -> list[RevenueDailyPoint]`.
  2. `use_cases.py`: `GetRevenueDaily(read_model, tenant_context)` — mismo esqueleto que `GetRevenueSummary`.
  3. `analytics_repo.py`: `SqlAlchemyRevenueDailyReadModel` — query:
     ```python
     day = func.date_trunc("day", SaleFactORM.occurred_at)
     stmt = (select(day, func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                    func.count(func.distinct(SaleFactORM.order_id)))
             .where(SaleFactORM.tenant_id == tenant_id)
             .group_by(day).order_by(day))
     ```
     con filtros opcionales since/until como el patrón READ_MODEL_SQL.
  4. `schemas/analytics.py`: `RevenueDailyPointResponse { day: date; sales_amount: int; orders_count: int }`.
  5. Router: `GET /analytics/revenue/daily` con `from`/`to` alias, `require_roles(Role.OWNER, Role.MANAGER)`, `response_model=list[RevenueDailyPointResponse]`.
  6. Container: factories `revenue_daily_read_model` + `get_revenue_daily` junto a los de analytics (container.py:853-872).
- **MIRROR**: los 4 patrones backend de arriba.
- **GOTCHA**: (1) Primer `date_trunc` del repo — trunca en UTC; días sin ventas NO vienen (el frontend rellena con 0). (2) No hay migración: solo lectura sobre `sale_facts` existente. (3) `day` llega como datetime tz-aware → convertir a `date` en el mapeo del read model.
- **VALIDATE**: integración en `test_e2e_analytics.py`: crear producto → orden → pago → `GET /api/v1/analytics/revenue/daily` → 1 bucket con `sales_amount` correcto; + test RLS (tenant 2 ve lista vacía). `pytest -q`.

### Task 13: Cliente + hook de la serie (frontend)
- **ACTION**: `types-analytics.ts`: `RevenueDailyPointDTO { day: string; sales_amount: number; orders_count: number }`. `analytics-api.ts`: `revenueDaily(query: AnalyticsQuery = {}): Promise<RevenueDailyPointDTO[]>` → `GET /analytics/revenue/daily` reusando el helper `period(query)`. `use-analytics.ts`: `useRevenueDaily(query)` key `["analytics-revenue-daily", query]`. Test en `analytics-api.test.ts` (patrón TEST_API_CLIENT).
- **VALIDATE**: `npm run test` + `npm run build`.

### Task 14: Dashboard Wellnod con datos reales (REWRITE)
- **ACTION**: Reescribir `dashboard-page.tsx` con el layout de tita (`git show 2497ebc -- frontend/src/features/dashboard/dashboard-page.tsx` como referencia visual) reemplazando TODOS los mocks:
  - **Header**: `Buen día{session.name ? `, ${session.name.split(" ")[0]}` : ""}` en `font-display text-3xl font-bold` + subtítulo "Esto es lo que pasa hoy en tu negocio" + fecha (helper `todayLabel()` de tita, con `new Date()` — OK en código de app).
  - **KPIs**: los 5 reales actuales (Ventas cobradas, Comandas activas, Ticket promedio, Egresos, Neto) de `useDashboard()`, en el estilo Card de tita (grid `sm:grid-cols-2 lg:grid-cols-4`, el 5° fluye), conservando `AnimatedNumber` + `formatMoney` + patrón pending→"—" del dashboard actual.
  - **Gráfico 7 días**: `useRevenueDaily({ from: <hoy-6d 00:00 ISO> })`; rellenar días faltantes con 0; barras estilo tita (`RevenueChart` sub-componente adaptado: max dinámico = max(valores)*1.1, ticks derivados, labels día corto es-AR); total del período en el header de la card.
  - **Recomendaciones IA**: `useFinanceOverview()` → `data.diagnostics` top 3 (orden: alert → warn → healthy), `RecommendationCard` de tita con tonos: alert→`border-l-destructive`, warn→`border-l-amber-500`, healthy→`border-l-primary`; footer link "Ver Finanzas →" a `/app/finanzas`. Si `configured === false` o sin diagnostics: card con CTA "Configurá tus costos en Finanzas".
  - **Medios de pago hoy**: `usePaymentMix({ from: <hoy 00:00 ISO> })` filtrando `direction === "IN"`; shares calculados sobre el total; `ProgressBar` de tita; labels legibles del `method` (mirror de cómo la pantalla de analytics/caja los muestra — revisar `frontend/src/features/analytics/` al implementar).
  - **Proyección de cierre** (reemplaza "punto de equilibrio" mock): `data.projection` de `useFinanceOverview` — proyectado de ventas + margen neto, `ProgressBar` con `elapsed_days/month_days`, leyenda "Día {elapsed} de {month_days}" (mirror del uso en `finance-page.tsx:90-178`). Si `projection === null`, ocultar la card.
  - **FAB**: `Link` a `/app/expenses`, `aria-label="Registrar egreso"`, estilo tita.
  - Sub-componentes `Card`, `ProgressBar`, `RevenueChart`, `RecommendationCard` copiados de tita y adaptados (Card con variante clara — ver GLASS_TITA).
- **GOTCHA**: (1) El dashboard solo lo ven OWNER/MANAGER (`RoleLanding` redirige a los demás) → los hooks de analytics/finance no necesitan gating por rol. (2) `useFinanceOverview()` sin args usa la ventana default del hook — OK. (3) NO borrar `AnimatedNumber`/`GradientHeading`/`TextureCard` de `components/ui` (otras pantallas los usan). (4) Montos en centavos: siempre `formatMoney`.
- **VALIDATE**: `npm run test && npm run build`; manual con datos reales del dev DB en claro y oscuro.

### Task 15: Validación integral Tanda Id-2
- **ACTION**: suite completa back+front igual que Task 11 + manual del dashboard con datos (crear ventas de prueba si el dev DB está vacío). Commit + merge `--no-ff` (mensaje `feat(dashboard): dashboard Wellnod con datos reales + serie diaria`).

---

## Testing Strategy

### Unit
| Test | Input | Expected | Edge |
|---|---|---|---|
| `test_get_my_profile` user con name | user(name="Juan Pérez"), tenant("La Trattoria") | MyProfile(name="Juan Pérez", tenant_name="La Trattoria", email=...) | |
| `test_get_my_profile` user sin name | user(name=None) | name=None (el front saluda sin nombre) | ✔ |
| `auth-api.test` me() | — | GET `/me` con `{auth:true}` | |
| `analytics-api.test` revenueDaily | `{from, to}` | GET `/analytics/revenue/daily?from=...` | sin query → sin `?` |

### Integración (backend, Postgres real)
- `/me`: onboard con `owner_name` → login → GET /me → name/email/tenant_name correctos. Onboard SIN owner_name → name null.
- `/analytics/revenue/daily`: venta pagada → 1 punto con monto; **RLS**: tenant 2 → `[]`.
- Onboarding sigue verde con y sin `owner_name` (campo opcional → sin breaking change).

### Edge Cases Checklist
- [ ] Usuario sin nombre (name null) → saludo "Buen día" pelado, iniciales desde email.
- [ ] Dev DB sin ventas → gráfico "Sin ventas en los últimos 7 días" (o barras en 0), payment mix vacío sin dividir por cero.
- [ ] `projection === null` / `configured === false` → cards degradan sin crashear.
- [ ] Modo claro Y oscuro en: login, shell, dashboard, drawer móvil.
- [ ] Cada rol ve su nav (OWNER 6+6+8 ítems; WAITER: Inicio, Clientes, Mesas, Fichar; KITCHEN: Inicio, Cocina, Fichar; BAR: Inicio, Barra, Fichar; CASHIER: Inicio, Clientes, Mesas, Caja, Propinas, Fichar).

## Validation Commands

```bash
# Backend (desde backend/)
alembic upgrade head          # aplica 0016 al dev DB
pytest                        # unit + integración (requiere Postgres)
# Frontend (desde frontend/)
npm run lint
npm run test                  # vitest
npm run build                 # ⚠️ GATE REAL: tsc -b && vite build (NUNCA tsc --noEmit)
```
EXPECT: todo verde, cero type errors. Manual: `npm run dev` → validar shell/dashboard en claro y oscuro.

## Acceptance Criteria
- [ ] Shell glass Wellnod en claro y oscuro; tema sigue al SO; toggle y ClockStatus presentes.
- [ ] Nav híbrida: TODAS las rutas actuales accesibles; gating por rol idéntico al actual.
- [ ] `GET /me` devuelve name/email/tenant_name; topbar muestra el local; avatar iniciales→logout.
- [ ] Onboarding acepta nombre opcional; emails firman Wellnod.
- [ ] Dashboard (solo OWNER/MANAGER): saludo, 5 KPIs reales, gráfico 7 días real, diagnostics reales, payment mix real, proyección real, FAB.
- [ ] Sin mocks residuales de tita (grep `Villapaz|Juan|Plan Pro|UNREAD_NOTIFICATIONS|BREAK_EVEN` en frontend/src → 0).
- [ ] Suites completas back y front verdes; `npm run build` verde.

## Completion Checklist
- [ ] Migración 0016 aplicada a dev; prod la aplica el preDeploy de Railway solo.
- [ ] Nuevos read models/use cases con `tenant_id` filter + tenant_context (Clean Architecture intacta: cero SQL en application, cero framework en domain).
- [ ] Tests siguen los patrones del repo (vi.fn HttpClient / _onboard_verify_login).
- [ ] Reporte en `.claude/PRPs/reports/identidad-wellnod-report.md`; plan movido a `completed/` al terminar.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Glass ilegible en modo claro | Media | Medio | Variantes `dark:` explícitas (GLASS_TITA); revisión manual en ambos temas es parte del gate |
| Cadena Alembic rota si Tanda C no mergeó | Media | Alto | Prerrequisito explícito arriba; verificar `alembic heads` = 0015 antes de crear 0016 |
| Session extendida rompe fixtures/tests | Alta | Bajo | Task 6 lista los archivos (guards.test, auth-api.test, DEV_SESSION); `npm run build` los caza |
| Nav híbrida pierde una ruta | Baja | Medio | Task 8 exige diff de cobertura contra nav-config actual; checklist por rol en edge cases |
| `date_trunc` UTC vs día local AR | Media | Bajo | Aceptado como MVP (documentado en NOT Building); el gráfico es tendencia, no contabilidad |
| Tests de email asserten "BRAVO" | Media | Bajo | grep en backend/tests como parte de Task 10 |

## Notes
- Fuente visual única: `git show 2497ebc` (rama `origin/tita`). Los snippets de tita citados acá fueron verificados contra ese commit.
- La marca en emails hoy es "BRAVO" (no "NÚCLEO" — eso solo vive en comentarios internos de MercadoPago que NO se tocan).
- `origin/pantallas` (otra rama nueva del remoto) no se analizó; fuera de alcance.
- Después de esta fase: retomar Finanzas D–F (renumerando migraciones) — ver memoria `plan-pantalla-finanzas`.
