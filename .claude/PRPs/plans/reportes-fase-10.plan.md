# Plan: Reportes (Fase 10) — reportes en pantalla + export para el contador

## Summary
Pantalla nueva **`/app/reportes`** que presenta los números del negocio por período (Hoy/Semana/Mes/Trimestre) en formato reporte (tablas + totales), **reusando los read models que ya existen** (analytics + finance + advisor + reports/staff), más una capa **net-new de export a CSV para el contador**: tres descargas (Ventas por día, Gastos itemizados, Libro IVA Ventas desde comprobantes AFIP). Sin WhatsApp, sin Excel/PDF, sin nuevas dependencias ni migraciones.

## User Story
Como **dueño/encargado (OWNER/MANAGER)** de un restaurante,
quiero **ver los reportes del período y descargarlos en CSV para pasárselos a mi contador**,
para **cerrar el mes y cumplir con la contabilidad sin armar planillas a mano**.

## Problem → Solution
Hoy los números viven repartidos entre Finanzas (salud/advisor), Home e IA/Insights, y **no hay ninguna forma de exportar datos** (cero endpoints de descarga en todo el backend) → una pantalla Reportes orientada a "período + tabla + exportar", que compone lo que ya se calcula y agrega **la primera capa de descarga de archivos** del producto (CSV UTF-8 con BOM, delimitador `;`, apto Excel-AR).

## Metadata
- **Complexity**: Large (~14 archivos: ~6 backend, ~8 frontend)
- **Source PRD**: NÚCLEO — Fase 10 (Reportes + Contador + WhatsApp). WhatsApp **fuera de scope** (trabado por decisión de proveedor).
- **PRD Phase**: Fase 10 (parcial: reportes + export contador)
- **Estimated Files**: ~14
- **Sin migraciones** (todas las tablas ya existen).

---

## UX Design

### Before
```
Nav lateral:  … Finanzas · [Reportes → /app/analytics (pantalla IA/Insights)] …
No existe pantalla de reportes por período. No hay export de nada.
El contador recibe capturas de pantalla / nada.
```

### After
```
Nav lateral:  … Finanzas · IA / Insights (→/app/analytics) · [Reportes (→/app/reportes)] …

/app/reportes:
┌─────────────────────────────────────────────────────────────┐
│  Reportes                     [Hoy][Semana][Mes*][Trimestre] │
│                                                               │
│  ┌── Resumen del período ─────────────────────────────────┐  │
│  │ Ventas $X · Cobrado $Y · Gastos $Z · Ganancia $N (m%)  │  │
│  │ Ticket prom. $T · Órdenes O · (proyección de mes)      │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌── Ventas por día ──┐ ┌── Gastos por rubro ─────────────┐  │
│  │ tabla + mini-barras│ │ categoría · monto · vs. previo  │  │
│  └────────────────────┘ └─────────────────────────────────┘  │
│  ┌── Top productos ───┐ ┌── Personal ─────────────────────┐  │
│  │ prod · unid · marg │ │ empleado · horas · ventas       │  │
│  └────────────────────┘ └─────────────────────────────────┘  │
│  ┌── Exportar para el contador ───────────────────────────┐  │
│  │ [Ventas (CSV)]  [Gastos (CSV)]  [Libro IVA Ventas (CSV)]│  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Nav "Reportes" | apunta a la pantalla IA (`/app/analytics`) | apunta a la nueva `/app/reportes`; la de IA se relabela "IA / Insights" | Reusa el gating OWNER/MANAGER |
| Ver números por período | repartido en Finanzas/Home | una pantalla reporte con selector de período | Reusa `finance-range.ts` |
| Pasar datos al contador | inexistente | 3 botones de descarga CSV del período actual | Primer patrón de descarga del producto |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/presentation/api/v1/reports.py` | todo (~21+) | Router `/reports` donde cuelgan los nuevos endpoints; patrón de `require_roles` + `Provide[Container.*]` + parseo `from`/`to`. |
| P0 | `backend/app/presentation/api/v1/finance.py` | 34, 158-219 | Patrón exacto de endpoint con ventana `from`/`to` (default mes en curso) y DI del use case (`GetExpenseBreakdown`, `GetRecentMovements`). Copiar el parseo de período. |
| P0 | `backend/app/application/finance/use_cases.py` | 297-360 | `ExpenseBreakdownReadModel`/`RecentMovementsReadModel` (ABC del read model) + `GetExpenseBreakdown`/`GetRecentMovements` (tenant_context + delega al read model). Molde de los use cases de export. |
| P0 | `backend/app/infrastructure/persistence/analytics_repo.py` | 33-139 | SQL de agregación por día sobre `sale_facts` (`date_trunc('day', occurred_at)`, `sum(line_amount)`, `sum(food_cost_amount)`, `count(distinct order_id)`, filtros `occurred_at >= since / <= until`). Base de `sales_rows`. |
| P0 | `backend/app/infrastructure/persistence/finance_repo.py` | 122-219 | SQL de egresos por categoría (`GROUP BY category`, OUTFLOW+CONFIRMED, `NULL→"Otros"`) y de movimientos IN/OUT por `created_at`. Base de `expense_rows`. |
| P0 | `backend/app/infrastructure/persistence/models.py` | 267-287, 323-346, 583-606 | Columnas exactas de `payments`, `invoices` y `sale_facts` (nombres de campos que van al CSV). |
| P0 | `backend/app/application/invoice/use_cases.py` | `ListInvoices` | Read model/repo de comprobantes ya existente; molde para `vat_sales_rows` (o reusarlo). Ver también `models.py:323-346` (columnas `net_amount, vat_amount, total_amount, cae, type, point_of_sale, number, doc_type, doc_number, issued_at, status`). |
| P0 | `backend/app/container.py` | providers de finance/analytics | Dónde y cómo se cablean read models + use cases (constructor injection). Agregar `report_export_read_model` + `report_exports`. |
| P1 | `backend/app/presentation/api/v1/realtime.py` | 42, 62 | Único `StreamingResponse` del repo (SSE). Referencia de cómo se devuelve algo que no es JSON; **no** es descarga — el patrón de `Response` con `Content-Disposition` es net-new. |
| P0 | `frontend/src/app/router.tsx` | 7-31, 74-90 | Registrar la ruta `/app/reportes` en el grupo `RequireRole allow={["OWNER","MANAGER"]}`. |
| P0 | `frontend/src/components/shell/nav-config.ts` | 41-116 | Relabelar "Reportes"→/app/analytics a "IA / Insights" y agregar "Reportes"→/app/reportes. |
| P0 | `frontend/src/api/http-client.ts` | 22-102 | `request<T>()` (auth Bearer + refresh 401 + `.text()→JSON`). Hay que **extraer el fetch+auth+refresh** a un método privado y agregar `download()` que devuelva Blob. Es lo más delicado del front. |
| P0 | `frontend/src/api/finance-api.ts` | todo | Molde de api client inyectable (ctor `HttpClient`, `qs()` builder, `request("GET", path, {auth:true})`). |
| P0 | `frontend/src/api/reports-api.ts` | todo | Client existente (`getDashboard`); acá se agregan las descargas CSV + `getStaff`. |
| P0 | `frontend/src/features/finance/finance-page.tsx` | 85-113, 138-215 | Molde de página: container `max-w-7xl`, `GradientHeading`, botones de período, gate loading/empty, `GlassCard`. |
| P0 | `frontend/src/lib/finance-range.ts` | 12-54 | `FINANCE_RANGES` + `rangeWindow(range)` → `{from,to}` ISO. Reusar tal cual para el selector de período. |
| P0 | `frontend/src/hooks/use-finance.ts` | 8-45 | Patrón de hook TanStack (`useServices()` + `useQuery`, `queryKey` con la ventana). Confirmar nombres exactos (`useFinanceOverview`, `useExpenseBreakdown`) y agregar los que falten. |
| P1 | `frontend/src/hooks/use-analytics.ts` | todo | Hooks de revenue/products; reusar `useRevenueDaily`/`useProductPerformance` (agregar thin wrapper si no existen). |
| P1 | `frontend/src/api/finance-api.test.ts` | 1-67 | Molde de test de api client (mock `request` con `vi.fn()`, assert method/path/options). |
| P1 | `frontend/src/lib/finance-range.test.ts` | 1-33 | Molde de test de helper puro (NOW fijo, vitest). |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| CSV en Python | stdlib `csv` + `io.StringIO` | Ya disponible (Python ≥3.12). No hay `pandas`/`openpyxl`/`reportlab` en `pyproject.toml` → **el formato es CSV, no Excel/PDF**. |
| Descarga en FastAPI | `fastapi.Response` con `media_type` + header `Content-Disposition: attachment; filename="..."` | No requiere `StreamingResponse` para archivos chicos; un `Response(content=str, media_type="text/csv; charset=utf-8")` alcanza. |
| CSV apto Excel-AR | convención | Prefijar **BOM `﻿`** (Excel detecta UTF-8) + delimitador **`;`** (Excel-AR usa `;` porque la coma es separador decimal) + montos con coma decimal (`1234,50`). |

> No external research needed más allá de esto — la feature usa patrones internos ya establecidos + `csv` stdlib.

---

## Patterns to Mirror

### NAMING_CONVENTION — read model ABC + use case (application)
```python
# SOURCE: backend/app/application/finance/use_cases.py:297-333 (parafraseado)
class ExpenseBreakdownReadModel(ABC):
    @abstractmethod
    async def breakdown(self, tenant_id: str, since: datetime, until: datetime) -> ExpenseBreakdown: ...

class GetExpenseBreakdown:
    def __init__(self, read_model: ExpenseBreakdownReadModel) -> None:
        self._read_model = read_model
    async def execute(self, tenant_id: str, since: datetime, until: datetime) -> ExpenseBreakdown:
        tenant_context.set(tenant_id)            # activa RLS
        return await self._read_model.breakdown(tenant_id, since, until)
```
> Los nuevos use cases de export siguen esto: dependen de un port `ReportExportReadModel`, setean `tenant_context`, delegan. Leer el archivo real para el import exacto de `tenant_context` y `ABC`.

### REPOSITORY_PATTERN — agregación tenant-scoped sobre sale_facts
```python
# SOURCE: backend/app/infrastructure/persistence/analytics_repo.py:33-71 (molde)
stmt = (
    select(
        func.date_trunc("day", SaleFactORM.occurred_at).label("day"),
        func.sum(SaleFactORM.line_amount),
        func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
        func.count(func.distinct(SaleFactORM.order_id)),
    )
    .where(
        SaleFactORM.tenant_id == tenant_id,
        SaleFactORM.occurred_at >= since,
        SaleFactORM.occurred_at <= until,
    )
    .group_by("day")
    .order_by("day")
)
```

### REPOSITORY_PATTERN — egresos itemizados (payments OUTFLOW)
```python
# SOURCE: backend/app/infrastructure/persistence/finance_repo.py:177-219 (molde)
stmt = (
    select(PaymentORM)
    .where(
        PaymentORM.tenant_id == tenant_id,
        PaymentORM.direction == PaymentDirection.OUTFLOW.value,
        PaymentORM.status == PaymentStatus.CONFIRMED.value,
        PaymentORM.created_at >= since,
        PaymentORM.created_at <= until,
    )
    .order_by(PaymentORM.created_at.desc())
)
```

### ROUTER_PATTERN — endpoint con ventana from/to + DI
```python
# SOURCE: backend/app/presentation/api/v1/finance.py:158-181 (molde)
@router.get("/expenses/breakdown", response_model=ExpenseBreakdownResponse)
@inject
async def get_expense_breakdown(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetExpenseBreakdown = Depends(Provide[Container.get_expense_breakdown]),
) -> ExpenseBreakdownResponse:
    since, until = _resolve_window(from_, to)   # default = mes en curso (copiar helper existente)
    ...
```
> **GOTCHA**: leer cómo `finance.py`/`analytics.py` resuelven el default de la ventana (mes en curso) y reutilizar ese mismo helper/lógica. No inventar uno nuevo.

### HOOK_PATTERN — TanStack sobre client inyectable
```ts
// SOURCE: frontend/src/hooks/use-finance.ts:8-14 (molde)
export function useFinanceOverview(query: FinanceQuery) {
  const { financeApi } = useServices()
  return useQuery({
    queryKey: ["finance-overview", query.from ?? null, query.to ?? null],
    queryFn: () => financeApi.overview(query),
  })
}
```

### API_CLIENT_PATTERN — client inyectable + qs()
```ts
// SOURCE: frontend/src/api/finance-api.ts (molde)
export class FinanceApi {
  constructor(private http: HttpClient) {}
  overview(query: FinanceQuery = {}): Promise<FinanceOverviewDTO> {
    return this.http.request("GET", `/finance/overview${this.qs(query)}`, { auth: true })
  }
  private qs(q: FinanceQuery): string { /* URLSearchParams */ }
}
```

### TEST_STRUCTURE — e2e integration (backend)
```python
# SOURCE: backend/tests/integration/test_e2e_preparations_api.py:44-78 (molde)
async def test_export_sales_csv(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # … crear insumo/producto/orden/pago para generar un sale_fact …
    resp = await http.get("/api/v1/reports/export/sales.csv", headers=h)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert "Ventas" in resp.text
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `backend/app/application/reporting/exports.py` | CREATE | Port `ReportExportReadModel` (ABC, 3 métodos) + dataclasses de fila (`SalesExportRow`, `ExpenseExportRow`, `VatSalesExportRow`) + use case `ReportExports` (3 métodos, tenant_context + delega). |
| `backend/app/infrastructure/persistence/report_export_repo.py` | CREATE | `SqlAlchemyReportExportReadModel`: 3 queries tenant-scoped (sale_facts por día, payments OUTFLOW, invoices por `issued_at`). |
| `backend/app/presentation/csv_export.py` | CREATE | Helper `csv_response(filename, header, rows) -> Response` (BOM + `;` + Content-Disposition) y `money(amount) -> "1234,50"`. Primer patrón de descarga del producto. |
| `backend/app/presentation/api/v1/reports.py` | UPDATE | 3 endpoints `GET /reports/export/{sales,expenses,vat-sales}.csv?from&to` (OWNER/MANAGER). |
| `backend/app/container.py` | UPDATE | Providers `report_export_read_model` + `report_exports`. |
| `backend/tests/integration/test_e2e_reports_export.py` | CREATE | e2e de los 3 CSV: 200 + headers + contenido + aislamiento por tenant. |
| `backend/tests/unit/test_csv_export.py` | CREATE | Unit del helper: header+filas→CSV, BOM, escaping de `;`/comillas, `money()`. |
| `frontend/src/api/http-client.ts` | UPDATE | Extraer `_fetch()` privado (auth+refresh) y agregar `download(path,{auth}) -> {blob, filename}` (parseo de `Content-Disposition`). |
| `frontend/src/api/reports-api.ts` | UPDATE | `downloadSalesCsv/ downloadExpensesCsv/ downloadVatSalesCsv(query)` (usan `http.download`) + `getStaff(query)`. |
| `frontend/src/lib/report-download.ts` (+`.test.ts`) | CREATE | `triggerDownload(blob, filename)` (createObjectURL + anchor click + revoke) y `parseContentDisposition()`. Helper puro testeable. |
| `frontend/src/features/reportes/reportes-page.tsx` | CREATE | La pantalla: selector de período + tablas (resumen, ventas/día, gastos/rubro, top productos, personal) + card de export con 3 botones. |
| `frontend/src/hooks/use-reportes.ts` (o extender use-finance/use-analytics) | CREATE/UPDATE | Hooks faltantes (`useRevenueDaily`, `useStaffReport`) si no existen; reusar los existentes. |
| `frontend/src/app/router.tsx` | UPDATE | Ruta `/app/reportes` en el grupo OWNER/MANAGER. |
| `frontend/src/components/shell/nav-config.ts` | UPDATE | Relabelar IA + agregar entrada "Reportes". |
| `frontend/src/api/reports-api.test.ts` | CREATE/UPDATE | Assert del shape de request de las descargas CSV. |

## NOT Building
- ❌ **Envío por WhatsApp** (Fase 10 completa) — trabado por decisión de proveedor. Explícitamente diferido.
- ❌ **Excel (.xlsx) ni PDF** — requerirían `openpyxl`/`reportlab` (no están en `pyproject.toml`). Solo CSV.
- ❌ **Envío por email / reportes programados / agendados**.
- ❌ **Nuevo endpoint JSON compuesto `/reports/period`** — la pantalla reusa los endpoints existentes (`/analytics/revenue*`, `/finance/expenses/breakdown`, `/analytics/products`, `/reports/staff`, `/finance/overview`). Menos riesgo, menos superficie.
- ❌ **Discriminación de IVA a nivel línea/venta** — los productos no guardan IVA; el IVA solo existe en comprobantes emitidos. El "Libro IVA Ventas" sale de la tabla `invoices` (comprobantes reales), no se recalcula.
- ❌ **Normalización de categorías de gasto** (son texto libre, `NULL→"Otros"`). El CSV las exporta tal cual.
- ❌ Migraciones / cambios de esquema.

---

## Step-by-Step Tasks

### Slice A — Backend: capa de export CSV (independiente, mergeable sola)

#### Task A1: Port + dataclasses + use case de export
- **ACTION**: Crear `backend/app/application/reporting/exports.py`.
- **IMPLEMENT**:
  - Dataclasses (frozen): `SalesExportRow(day: date, sales_amount: int, food_cost_amount: int, orders_count: int)`, `ExpenseExportRow(occurred_at: datetime, category: str, counterparty: str | None, description: str | None, method: str, amount: int)`, `VatSalesExportRow(issued_at: datetime, type: str, point_of_sale: int, number: int, doc_type: str, doc_number: str, net_amount: int, vat_amount: int, total_amount: int, total_currency: str, cae: str | None, status: str)`.
  - `class ReportExportReadModel(ABC)` con 3 métodos async abstractos: `sales_rows(tenant_id, since, until) -> list[SalesExportRow]`, `expense_rows(...) -> list[ExpenseExportRow]`, `vat_sales_rows(...) -> list[VatSalesExportRow]`.
  - `class ReportExports` (un solo use case-facade de solo lectura): ctor recibe el port; 3 métodos `sales/expenses/vat_sales(tenant_id, since, until)` que hacen `tenant_context.set(tenant_id)` y delegan.
- **MIRROR**: read model ABC + use case de `use_cases.py:297-333`.
- **IMPORTS**: `from abc import ABC, abstractmethod`; `from dataclasses import dataclass`; `from datetime import date, datetime`; el `tenant_context` que usa `GetExpenseBreakdown` (leer el import exacto en `app/application/finance/use_cases.py`).
- **GOTCHA**: `domain`/`application` no importan SQLAlchemy. Las dataclasses son puras. Justificación del facade único: familia de exports de solo-lectura sin invariantes por operación (aceptable bajo SOLID; el reviewer puede partir en 3 si lo prefiere).
- **VALIDATE**: `poetry run ruff check app/application/reporting/exports.py`.

#### Task A2: Read model SQLAlchemy
- **ACTION**: Crear `backend/app/infrastructure/persistence/report_export_repo.py`.
- **IMPLEMENT**: `class SqlAlchemyReportExportReadModel(ReportExportReadModel)` con `SessionFactory`:
  - `sales_rows`: query de `analytics_repo.py:33-71` (group by `date_trunc('day', occurred_at)`, sum line/food, count distinct order), mapear a `SalesExportRow`.
  - `expense_rows`: query de `finance_repo.py:177-219` filtrando `direction==OUTFLOW & status==CONFIRMED` por `created_at` en `[since, until]`; `category or "Otros"`; mapear a `ExpenseExportRow`.
  - `vat_sales_rows`: `select(InvoiceORM).where(tenant_id==…, issued_at>=since, issued_at<=until).order_by(issued_at)` → mapear a `VatSalesExportRow` (columnas de `models.py:323-346`).
- **MIRROR**: `analytics_repo.py` / `finance_repo.py` (misma forma de sesión y filtros).
- **IMPORTS**: `from sqlalchemy import select, func`; ORMs `SaleFactORM, PaymentORM, InvoiceORM` de `app.infrastructure.persistence.models`; enums `PaymentDirection, PaymentStatus`.
- **GOTCHA**: `sale_facts` filtra por `occurred_at`; `payments` por `created_at` (no tiene fecha contable separada). Todas las queries **filtran `tenant_id`** explícitamente (además de RLS). Manejar `food_cost_amount` nullable con `coalesce(..., 0)`.
- **VALIDATE**: `poetry run ruff check` + se prueba vía el e2e de A5.

#### Task A3: Helper de CSV (presentación) + patrón de descarga
- **ACTION**: Crear `backend/app/presentation/csv_export.py`.
- **IMPLEMENT**:
  ```python
  import csv, io
  from collections.abc import Iterable, Sequence
  from fastapi import Response

  def money(amount_centavos: int) -> str:
      return f"{amount_centavos / 100:.2f}".replace(".", ",")

  def csv_response(filename: str, header: Sequence[str],
                   rows: Iterable[Sequence[object]]) -> Response:
      buf = io.StringIO()
      writer = csv.writer(buf, delimiter=";")
      writer.writerow(header)
      writer.writerows(rows)
      body = "﻿" + buf.getvalue()  # BOM → Excel detecta UTF-8
      return Response(
          content=body,
          media_type="text/csv; charset=utf-8",
          headers={"Content-Disposition": f'attachment; filename="{filename}"'},
      )
  ```
- **MIRROR**: es net-new; `realtime.py:62` sólo como referencia de "devolver algo no-JSON".
- **GOTCHA**: BOM + `delimiter=";"` son **obligatorios** para que el contador lo abra bien en Excel-AR (coma = separador decimal). No usar `,`.
- **VALIDATE**: cubierto por unit test A6.

#### Task A4: Endpoints CSV en el router `/reports`
- **ACTION**: Editar `backend/app/presentation/api/v1/reports.py`.
- **IMPLEMENT**: 3 endpoints (sin `response_model`, devuelven `Response`):
  - `GET /reports/export/sales.csv` → `use_case.sales(...)` → `csv_response("ventas_<periodo>.csv", ["Fecha","Ventas","Food cost","Órdenes"], [(r.day.isoformat(), money(r.sales_amount), money(r.food_cost_amount), r.orders_count) for r in rows])`.
  - `GET /reports/export/expenses.csv` → header `["Fecha","Categoría","Contraparte","Descripción","Método","Monto"]`.
  - `GET /reports/export/vat-sales.csv` → header `["Fecha","Tipo","Pto vta","Número","Doc tipo","Doc receptor","Neto","IVA","Total","CAE","Estado"]`.
  - Todos: `require_roles(Role.OWNER, Role.MANAGER)`, ventana `from`/`to` con el **mismo default (mes en curso)** que `finance.py`, `Depends(Provide[Container.report_exports])`.
- **MIRROR**: `finance.py:158-181` (parseo de ventana + DI).
- **IMPORTS**: `from fastapi import Query, Depends, Response`; `from app.presentation.csv_export import csv_response, money`.
- **GOTCHA**: reutilizar el helper de resolución de ventana existente (no duplicar). El nombre de archivo puede incluir el período (ej. `ventas_2026-08.csv`) o quedarse fijo — cualquiera sirve; mantener simple.
- **VALIDATE**: `poetry run ruff check` + e2e A5.

#### Task A5: Wiring en el container
- **ACTION**: Editar `backend/app/container.py`.
- **IMPLEMENT**: provider `report_export_read_model = providers.Singleton(SqlAlchemyReportExportReadModel, session_factory=...)` (mirror de otros read models) + `report_exports = providers.Factory(ReportExports, read_model=report_export_read_model)`.
- **MIRROR**: providers de `get_expense_breakdown` / `get_recent_movements` en el mismo archivo.
- **GOTCHA**: ruff ordena imports; correr `--fix`. Verificar que el router está `@inject`-ado y el `Container` wira el módulo `reports`.
- **VALIDATE**: `poetry run pytest tests/integration/test_e2e_reports_export.py`.

#### Task A6: Tests backend
- **ACTION**: Crear `backend/tests/unit/test_csv_export.py` + `backend/tests/integration/test_e2e_reports_export.py`.
- **IMPLEMENT**:
  - Unit: `csv_response` con filas conocidas → assert BOM al inicio, delimitador `;`, escaping de un campo con `;`/comillas/salto de línea (lo hace `csv.writer`), `Content-Disposition` con `attachment`. `money(123450) == "1234,50"`, `money(0) == "0,00"`, negativos.
  - e2e (3 tests): onboard+login; generar un sale_fact (crear producto + orden + pago que la settle → dispara `ProjectOrderSales`) y un gasto (`POST /expenses`); pegar a cada `*.csv` y assert 200 + `text/csv` + `attachment` + que el body contiene los datos. Un test de **aislamiento**: tenant B no ve filas de A. Para `vat-sales.csv`, si generar un comprobante real es costoso, basta assert 200 + header aunque el body sólo tenga la fila de header (documentar).
- **MIRROR**: `test_e2e_preparations_api.py` (fixtures `_onboard_verify_login`, `_auth`, `client`) y `test_e2e_auth.py`.
- **GOTCHA**: `asyncio_mode = "auto"` → **no** poner `@pytest.mark.anyio`. Migraciones ya aplicadas (`poetry run alembic upgrade head` sobre `bravo_dev`). Reusar los helpers `_ingredient/_product` de los e2e existentes para generar ventas.
- **VALIDATE**: `poetry run pytest` (suite completa verde, sin regresiones) + `poetry run ruff check`.

### Slice B — Frontend: pantalla Reportes + descarga (depende de A)

#### Task B1: Descarga autenticada en HttpClient
- **ACTION**: Editar `frontend/src/api/http-client.ts`.
- **IMPLEMENT**: Extraer el core (fetch + header Bearer + refresh 401) a un privado `_fetch(method, path, options): Promise<Response>`; `request<T>` pasa a `const res = await this._fetch(...); return JSON.parse(await res.text())` (comportamiento idéntico). Agregar:
  ```ts
  async download(path: string, options: { auth?: boolean } = {}): Promise<{ blob: Blob; filename: string }> {
    const res = await this._fetch("GET", path, options)
    if (!res.ok) throw await this.toApiError(res)     // reusar el mapeo existente
    const blob = await res.blob()
    const filename = parseContentDisposition(res.headers.get("Content-Disposition")) ?? "reporte.csv"
    return { blob, filename }
  }
  ```
- **MIRROR**: la lógica de auth/refresh/errores ya en `http-client.ts:43-102` — **no reescribirla**, extraerla.
- **GOTCHA**: es el cambio más delicado del front (toca el path de auth compartido por toda la app). Refactor mínimo y verificar que los tests existentes de api clients siguen verdes. `parseContentDisposition` va en `report-download.ts` (B2) e se importa acá.
- **VALIDATE**: `npm run build` + `npm run test` (no romper tests de otros clients).

#### Task B2: Helper de descarga puro
- **ACTION**: Crear `frontend/src/lib/report-download.ts` + `report-download.test.ts`.
- **IMPLEMENT**:
  ```ts
  export function parseContentDisposition(header: string | null): string | null {
    if (!header) return null
    const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header)
    return m ? decodeURIComponent(m[1]) : null
  }
  export function triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url; a.download = filename
    document.body.appendChild(a); a.click(); a.remove()
    URL.revokeObjectURL(url)
  }
  ```
- **GOTCHA**: `triggerDownload` toca el DOM → testear sólo `parseContentDisposition` (puro) en vitest; `triggerDownload` se valida manual. `report-download.ts` **no exporta componentes** (evita el warning de react-refresh).
- **VALIDATE**: `npm run test src/lib/report-download.test.ts` + `npm run lint`.

#### Task B3: reports-api.ts — descargas + staff
- **ACTION**: Editar `frontend/src/api/reports-api.ts`.
- **IMPLEMENT**: `downloadSalesCsv(q)`, `downloadExpensesCsv(q)`, `downloadVatSalesCsv(q)` → `this.http.download('/reports/export/sales.csv' + qs(q), { auth: true })`. `getStaff(q) -> Promise<StaffReportDTO[]>` → `request("GET", '/reports/staff'+qs(q), {auth:true})`. Reusar/duplicar el `qs()` de `finance-api.ts`. Tipos DTO en `src/api/types-operations.ts`.
- **MIRROR**: `finance-api.ts` (`qs()` + `request`).
- **VALIDATE**: `npm run build`.

#### Task B4: Hooks
- **ACTION**: Crear `frontend/src/hooks/use-reportes.ts` (o extender los existentes).
- **IMPLEMENT**: Confirmar qué hooks ya existen (`useFinanceOverview`, `useExpenseBreakdown` en `use-finance.ts`; `useRevenueDaily`/`useProductPerformance` en `use-analytics.ts`). Agregar los faltantes como thin wrappers (`useServices()` + `useQuery`, `queryKey` con la ventana). `useStaffReport(query)` → `reportsApi.getStaff(query)`. Las descargas NO usan `useQuery` (son acciones); exponer un `useMutation` o simplemente llamar `reportsApi.downloadX` + `triggerDownload` en un handler.
- **MIRROR**: `use-finance.ts:8-14`.
- **GOTCHA**: no re-fetch en cada render; `queryKey` estable con `query.from ?? null, query.to ?? null`.
- **VALIDATE**: `npm run build`.

#### Task B5: Pantalla `reportes-page.tsx`
- **ACTION**: Crear `frontend/src/features/reportes/reportes-page.tsx`.
- **IMPLEMENT**: `export function ReportesPage()`:
  - Estado de período: `const [range, setRange] = useState<FinanceRange>("month"); const window = useMemo(() => rangeWindow(range), [range])`. Botones `FINANCE_RANGES`.
  - Datos: `useFinanceOverview(window)` (resumen/KPIs/proyección), `useExpenseBreakdown(window)` (gastos por rubro), `useRevenueDaily(window)` (serie), `useProductPerformance(window)` (top), `useStaffReport(window)` (personal).
  - Layout: container `mx-auto max-w-7xl px-6 py-8`, `GradientHeading`, gate loading/empty por card, `GlassCard` para cada sección. Tablas simples (shadcn `Table` como en `analytics-page.tsx`) + mini-barras a mano (`div` con `style height %`) si se quiere para "ventas por día".
  - Card **"Exportar para el contador"**: 3 `Button` que llaman `const { blob, filename } = await reportsApi.downloadSalesCsv(window); triggerDownload(blob, filename)` con toast de error (`isApiError`). Deshabilitar mientras descarga.
- **MIRROR**: `finance-page.tsx:85-215` (composición) + `analytics-page.tsx:121-150` (tablas + empty states).
- **GOTCHA**: mantener la página **fina** (lógica de agregación/format en helpers puros si hace falta). No `fetch` suelto — todo por hooks/clients. Formatear montos con el helper `money`/`formatMoney` existente de `src/lib/money.ts`.
- **VALIDATE**: `npm run build` + revisión visual.

#### Task B6: Ruta + nav
- **ACTION**: Editar `frontend/src/app/router.tsx` y `frontend/src/components/shell/nav-config.ts`.
- **IMPLEMENT**:
  - router: `import { ReportesPage } from "@/features/reportes/reportes-page"` + `{ path: "/app/reportes", element: <ReportesPage /> }` en el grupo `RequireRole allow={["OWNER","MANAGER"]}`.
  - nav: cambiar la entrada actual `{ label: "Reportes", to: "/app/analytics", icon: FileText, roles: ["OWNER","MANAGER"] }` a `{ label: "IA / Insights", to: "/app/analytics", icon: Sparkles, ... }` y **agregar** `{ label: "Reportes", to: "/app/reportes", icon: FileText, roles: ["OWNER","MANAGER"] }`.
- **MIRROR**: entradas existentes en `nav-config.ts:41-116`.
- **GOTCHA**: importar el ícono nuevo (`Sparkles`) de `lucide-react`. El gating real es la ruta (`RequireRole`), el nav es cosmético.
- **VALIDATE**: `npm run build` + navegar como OWNER y como WAITER (no debe ver la ruta).

#### Task B7: Tests frontend
- **ACTION**: Crear `frontend/src/api/reports-api.test.ts` (+ el de `report-download.test.ts` de B2).
- **IMPLEMENT**: mock de `download`/`request` con `vi.fn()`, assert method/path (`/reports/export/sales.csv`, incluye `from=`/`to=`) y `{auth:true}`.
- **MIRROR**: `finance-api.test.ts:1-67`.
- **VALIDATE**: `npm run test`.

---

## Testing Strategy

### Unit Tests
| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| `money()` | `123450` / `0` / `-500` | `"1234,50"` / `"0,00"` / `"-5,00"` | sí (cero, negativo) |
| `csv_response` | header + 2 filas | body empieza con `﻿`, usa `;`, `Content-Disposition: attachment` | — |
| `csv` escaping | campo con `;` y `"` | `csv.writer` lo entrecomilla correctamente | sí |
| `parseContentDisposition` | `attachment; filename="ventas.csv"` / `null` | `"ventas.csv"` / `null` | sí (null/UTF-8'') |
| `rangeWindow` (reuso) | ya cubierto por `finance-range.test.ts` | — | — |

### Edge Cases Checklist
- [x] Período sin ventas → CSV con sólo la fila de header (no 500).
- [x] Gasto con `category = NULL` → exporta `"Otros"`.
- [x] Sin comprobantes AFIP → `vat-sales.csv` con sólo header.
- [x] Montos grandes / negativos (reembolsos) → `money()` correcto.
- [x] Aislamiento por tenant (RLS + filtro) → tenant B no ve filas de A.
- [x] Rol WAITER/KITCHEN → 403 en endpoints y ruta oculta.
- [x] Campo con `;` o comillas → no rompe columnas (csv.writer).

---

## Validation Commands

### Backend
```bash
cd backend && poetry run ruff check --fix
cd backend && poetry run pytest            # suite completa, sin regresiones (base ~400 tests)
```
EXPECT: 0 errores ruff, todos los tests verdes (400 previos + nuevos).

### Frontend
```bash
cd frontend && npm run build               # tsc -b && vite build — el gate real
cd frontend && npm run test                # vitest
cd frontend && npm run lint                # eslint (react-refresh: helpers no exportan componentes)
```
EXPECT: build sin errores de tipo, tests verdes, lint limpio.

### Database
```bash
cd backend && poetry run alembic upgrade head   # NO debe crear migración nueva (feature sin schema change)
```
EXPECT: "up to date" (head = 0021, sin cambios).

### Manual
- [ ] Login OWNER (o `VITE_AUTH_BYPASS`) → nav muestra "Reportes" + "IA / Insights" separados.
- [ ] `/app/reportes` carga con datos reales; cambiar período recalcula todo.
- [ ] Descargar los 3 CSV; abrir en Excel/LibreOffice → columnas y acentos correctos, montos con coma decimal.
- [ ] Login WAITER → no aparece "Reportes"; entrar por URL → "No tenés permisos".
- [ ] Visual claro/oscuro (tema del SO + toggle).

---

## Acceptance Criteria
- [ ] Pantalla `/app/reportes` con selector de período y las secciones de resumen/ventas/gastos/top/personal, reusando read models existentes.
- [ ] 3 descargas CSV (ventas, gastos, libro IVA ventas) del período seleccionado, con BOM + `;` (aptas Excel-AR).
- [ ] Endpoints protegidos OWNER/MANAGER; aislamiento por tenant probado.
- [ ] Todas las validaciones (backend + frontend + db) pasan sin regresiones.
- [ ] Sin migraciones, sin nuevas dependencias.

## Completion Checklist
- [ ] Read model ABC en application, impl en infrastructure (nada de SQLAlchemy en application/domain).
- [ ] `tenant_context` seteado en cada use case; toda query filtra `tenant_id`.
- [ ] Errores de API con `code` (EN) + `message` (ES) donde aplique (los CSV devuelven `Response` directo).
- [ ] Tests siguen los patrones (`asyncio_mode=auto`, fixtures e2e existentes, vitest colocado).
- [ ] Front: datos por clients inyectables + hooks, sin `fetch` suelto en componentes.
- [ ] Commit por slice, merge `--no-ff`, push origin main; reporte en `.claude/PRPs/reports/`.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Refactor de `HttpClient` (extraer `_fetch`) rompe el auth/refresh compartido | Media | Alto | Refactor mínimo (mover, no reescribir); correr todos los `*-api.test.ts` + probar login/refresh manual antes de mergear. |
| Colisión de nombre "Reportes" (nav ya lo usa para Analytics) | Alta | Bajo | Relabelar Analytics a "IA / Insights" en el mismo cambio (Task B6). |
| CSV mal codificado en Excel-AR (acentos/columnas) | Media | Medio | BOM `﻿` + `delimiter=";"` + validación manual abriendo en Excel. |
| `vat-sales.csv` vacío si no se emiten comprobantes en el MVP | Alta | Bajo | Comportamiento correcto (header only); documentar; el valor real aparece cuando se factura por AFIP. |
| Desalineación de ventana: `sale_facts.occurred_at` vs `payments.created_at` | Baja | Bajo | Documentado; cada CSV usa la fecha correcta de su fuente; consistente con analytics/finance actuales. |
| `ListInvoices`/columnas de `invoices` distintas a lo asumido | Media | Medio | P0 mandatory-read de `models.py:323-346` + `application/invoice/use_cases.py` antes de codear `vat_sales_rows`. |

## Notes
- **Corrección de contexto**: al explorar se confirmó que **AFIP/facturación electrónica YA está construida** (dominio `invoice`, adapter WSAA/WSFEv1 real + fake, tabla `invoices`, `IssueInvoice`/`ListInvoices`, routers `invoices.py`/`tax.py`). Esto habilita el "Libro IVA Ventas" con datos fiscales reales (CAE incluido), no un stub. (La memoria decía "AFIP no arrancado" — actualizar.)
- **Sin dato de comisiones**: `payments` no guarda fee de pasarela → los cobros netos de comisión no son exportables (limitación conocida, ya documentada en Home v2).
- **Slicing sugerido**: Slice A (backend export, mergeable solo — deja la API lista) → Slice B (frontend pantalla + descarga). Igual que las tandas previas del proyecto.
- **Por qué CSV y no Excel/PDF**: no hay `openpyxl`/`reportlab` en el proyecto; agregar dep queda para una iteración futura si el contador lo pide. CSV cubre el 90% del caso (todo contador importa CSV).
- **Datos-fuente por CSV**: ventas ← `sale_facts` (por día); gastos ← `payments` OUTFLOW CONFIRMED; libro IVA ← `invoices`. Todos ya consultables por ventana temporal.
