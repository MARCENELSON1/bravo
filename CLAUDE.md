# CLAUDE.md — BRAVO

Reglas vinculantes del proyecto. Léelas antes de escribir o planificar código.

## Qué es

SaaS **multi-tenant** de operaciones para PyMEs de hospitality (restaurantes primero; hoteles/turismo en fases futuras).
**Wedge MVP — "El cerebro del local":** comandas digitales (mozo→cocina/KDS) + cobro/facturación + fichaje de empleados + **copiloto IA** (consultas en lenguaje natural sobre el negocio).
**Diferenciador:** copiloto conversacional en español + AFIP nativo (ver `.claude/PRPs/research/mercado-hospitality-ar.md`).

## Stack

- **Frontend:** Vite + React 19 + TypeScript + Tailwind v4 + shadcn. Design system: **Cult UI** (registro `@cult-ui` vía MCP de shadcn).
- **Backend:** **FastAPI (Python)**, separado del frontend.
- **DB:** PostgreSQL. **IA:** Anthropic (Claude). **Facturación:** AFIP/ARCA — **Build** (adapter propio, reversible a Buy).

## Arquitectura (NO negociable)

Backend en **Clean Architecture + Ports & Adapters + SOLID + Repository + DI por contenedor (`dependency-injector`)**.
**Guía completa y obligatoria:** `docs/architecture/backend-clean-architecture.md`. Resumen de las reglas:

- **Regla de oro:** las dependencias apuntan hacia adentro: `presentation → application → domain ← infrastructure`.
- `domain` es Python puro: **no importa** FastAPI, SQLAlchemy ni `anthropic`.
- Los casos de uso (`application`) dependen de **ports** (interfaces), nunca de implementaciones.
- Todo servicio externo (AFIP, LLM, pagos, DB) vive **detrás de un port** con su adapter en `infrastructure`.
- La DI se cablea en `container.py` y se inyecta por constructor. En tests se hace `override` de los providers con fakes.
- **Multi-tenant:** toda query filtra por `tenant_id`; RLS en Postgres como red de seguridad.

### Prohibido
- ❌ Lógica de negocio en routers FastAPI o en modelos ORM.
- ❌ Importar frameworks desde `domain`/`application`.
- ❌ Instanciar adapters a mano dentro de un caso de uso (se inyectan).
- ❌ Queries sin filtro de `tenant_id`.
- ❌ Confundir entidad de dominio / modelo ORM / schema Pydantic (son 3 cosas, con mappers entre ellas).

## Frontend

- Componentes de UI desde **Cult UI** vía MCP de shadcn (`mcp__shadcn__*`, registro `@cult-ui`). Antes de codear un componente a mano, buscá si Cult UI ya lo tiene.
- Separación por capas también en el front: UI (componentes) / estado / **datos (clientes de API inyectables, no `fetch` suelto en componentes)**.

## Convenciones

- **Ubiquitous language en español** para el dominio (`Comanda`, `Mesa`, `Mozo`, `Turno`, `Comprobante`); plomería técnica en inglés.
- Cobertura de tests **80%+** en dominio y casos de uso.

## Flujo de trabajo (spec-driven / PRP)

1. PRD en `.claude/PRPs/prds/` (`/prp-prd`).
2. Plan por fase en `.claude/PRPs/` (`/prp-plan`).
3. Implementación con validación (`/prp-implement`).
- Investigación de mercado: `.claude/PRPs/research/mercado-hospitality-ar.md`.

## Notas del entorno

- Hay un hook **GateGuard** que exige declarar hechos antes del primer `Bash` y antes de cada escritura. Cumplir y reintentar.
- Idioma del usuario: **español rioplatense (Argentina)**. Responder en español.
