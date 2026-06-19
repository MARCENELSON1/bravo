# Guía de Arquitectura — Backend (FastAPI + Clean Architecture)

> **Estado:** vinculante. Todo el backend se construye siguiendo este documento.
> **Proyecto:** BRAVO — SaaS multi-tenant de operaciones para restaurantes (wedge MVP: comandas + cobro/facturación + fichaje + copiloto IA).

---

## 0. Decisiones (mini-ADR)

| Decisión | Elección | Por qué |
|---|---|---|
| Backend | **FastAPI (Python)** | Ecosistema de IA #1 (el copiloto es el diferenciador), `pyafipws` maduro para AFIP, velocidad de desarrollo. |
| Arquitectura | **Clean Architecture + Ports & Adapters** | Cambios sin reconstrucciones que rompan: la lógica de negocio no depende de DB/AFIP/IA. |
| Principios | **SOLID** | Código extensible y testeable. |
| Acceso a datos | **Repository pattern** | El dominio habla con interfaces, no con SQLAlchemy. |
| Inversión de control | **DI por contenedor (`dependency-injector`)** | El `Depends` de FastAPI es por-request; queremos un contenedor IoC real con override en tests. |
| Multi-tenant | **`tenant_id` en contexto + filtrado en repos + RLS Postgres** | Aislamiento con red de seguridad a nivel base. |
| Facturación AFIP | **Build** (adapter propio), reversible a Buy | Detrás de un port → cambiar a middleware = cambiar un adapter, no la lógica. |

---

## 1. La regla de oro: las dependencias apuntan hacia ADENTRO

```
  presentation ──▶ application ──▶ domain ◀── infrastructure
   (FastAPI)        (casos de uso)   (puro)     (adapters: DB, AFIP, LLM)
```

- **`domain`** no importa NADA de las otras capas ni de frameworks. Es Python puro.
- **`application`** depende sólo de `domain` (de sus **ports/interfaces**, nunca de implementaciones).
- **`infrastructure`** y **`presentation`** dependen hacia adentro. La infra **implementa** los ports del dominio.
- **Nunca** una capa interna importa una externa. Si te tienta, es señal de que el límite está mal.

### SOLID, aplicado a este proyecto
- **S** (responsabilidad única): un caso de uso = una intención (`AbrirComanda`, `CerrarYFacturar`).
- **O** (abierto/cerrado): se agregan adapters nuevos sin tocar el código existente → **el caso AFIP Build→Buy**.
- **L** (sustitución): cualquier adapter respeta el contrato del port y es intercambiable.
- **I** (segregación): ports chicos y específicos (`ComandaRepository`, no un "RepositorioGigante").
- **D** (inversión): los casos de uso dependen de abstracciones; la DI inyecta la implementación concreta.

---

## 2. Estructura de carpetas

```
backend/
├─ app/
│  ├─ domain/                      # CAPA 1 — pura, sin frameworks
│  │  ├─ comanda/
│  │  │  ├─ entities.py            #   Comanda, ItemComanda
│  │  │  ├─ value_objects.py       #   Dinero, EstadoComanda
│  │  │  ├─ exceptions.py          #   ComandaNoEncontrada, ComandaNoModificable
│  │  │  └─ repository.py          #   ComandaRepository (PORT, ABC)
│  │  ├─ empleado/                 #   Empleado, Turno (fichaje) + EmpleadoRepository
│  │  ├─ facturacion/
│  │  │  ├─ entities.py            #   Comprobante, SolicitudComprobante
│  │  │  └─ ports.py               #   FacturacionElectronica (PORT)
│  │  └─ copiloto/
│  │     └─ ports.py               #   CopilotoLLM (PORT)
│  ├─ application/                 # CAPA 2 — casos de uso, dependen de PORTS
│  │  ├─ comanda/
│  │  │  ├─ abrir_comanda.py
│  │  │  ├─ cerrar_y_facturar.py
│  │  │  └─ dtos.py                #   DTOs de entrada/salida del caso de uso
│  │  └─ copiloto/
│  │     └─ preguntar.py
│  ├─ infrastructure/              # CAPA 3 — adapters (implementan los ports)
│  │  ├─ persistence/
│  │  │  ├─ database.py            #   engine + session factory (async SQLAlchemy)
│  │  │  ├─ models.py              #   modelos ORM (¡SEPARADOS de las entities!)
│  │  │  ├─ mappers.py             #   ORM ⇄ entidad de dominio
│  │  │  └─ comanda_repo.py        #   SqlAlchemyComandaRepository
│  │  ├─ afip/
│  │  │  └─ afip_directo.py        #   AfipDirectoFacturacion (Build)
│  │  └─ llm/
│  │     └─ anthropic_copiloto.py  #   AnthropicCopiloto (text-to-SQL con guardrails)
│  ├─ presentation/                # CAPA 4 — FastAPI (routers finos)
│  │  ├─ api/v1/
│  │  │  ├─ comandas.py
│  │  │  └─ copiloto.py
│  │  ├─ schemas/                  #   Pydantic request/response (NO son las entities)
│  │  ├─ errors.py                 #   mapea excepciones de dominio → HTTP
│  │  └─ deps.py                   #   dependencia de tenant/usuario actual
│  ├─ container.py                 # Contenedor de DI (cablea ports → adapters)
│  ├─ config.py                    # Settings (pydantic-settings)
│  └─ main.py                      # app factory + middleware + wiring
├─ tests/
│  ├─ unit/                        # dominio + casos de uso (con fakes, sin DB)
│  └─ integration/                 # adapters reales (DB, AFIP sandbox)
├─ alembic/                        # migraciones
└─ pyproject.toml
```

---

## 3. Capa 1 — Domain (puro)

**Entidades** (reglas de negocio, sin saber de DB/HTTP/IA):

```python
# domain/comanda/entities.py
from dataclasses import dataclass, field
from app.domain.comanda.value_objects import Dinero, EstadoComanda
from app.domain.comanda.exceptions import ComandaNoModificable

@dataclass
class ItemComanda:
    producto_id: str
    nombre: str
    cantidad: int
    precio_unit: Dinero

@dataclass
class Comanda:
    id: str
    tenant_id: str
    mesa_id: str
    mozo_id: str
    estado: EstadoComanda
    items: list[ItemComanda] = field(default_factory=list)

    def agregar_item(self, item: ItemComanda) -> None:
        if self.estado is not EstadoComanda.ABIERTA:
            raise ComandaNoModificable(self.id)
        self.items.append(item)

    def total(self) -> Dinero:
        return sum((i.precio_unit * i.cantidad for i in self.items), Dinero.cero())
```

**Port de repositorio** (interfaz; vive en el dominio porque el dominio define QUÉ necesita):

```python
# domain/comanda/repository.py
from abc import ABC, abstractmethod
from app.domain.comanda.entities import Comanda

class ComandaRepository(ABC):
    @abstractmethod
    async def obtener(self, comanda_id: str, tenant_id: str) -> Comanda | None: ...
    @abstractmethod
    async def guardar(self, comanda: Comanda) -> None: ...
```

**Port de servicio externo** (AFIP, IA → también interfaces del dominio):

```python
# domain/facturacion/ports.py
from abc import ABC, abstractmethod
from app.domain.facturacion.entities import Comprobante, SolicitudComprobante

class FacturacionElectronica(ABC):
    @abstractmethod
    async def emitir(self, solicitud: SolicitudComprobante) -> Comprobante: ...
```

---

## 4. Capa 2 — Application (casos de uso)

Orquestan el dominio. **Reciben los ports por el constructor** (DI). No saben qué implementación corre.

```python
# application/comanda/cerrar_y_facturar.py
from app.domain.comanda.repository import ComandaRepository
from app.domain.facturacion.ports import FacturacionElectronica
from app.domain.facturacion.entities import Comprobante, SolicitudComprobante
from app.domain.comanda.exceptions import ComandaNoEncontrada

class CerrarYFacturar:
    def __init__(self, comandas: ComandaRepository, facturacion: FacturacionElectronica):
        self._comandas = comandas
        self._facturacion = facturacion

    async def ejecutar(self, comanda_id: str, tenant_id: str) -> Comprobante:
        comanda = await self._comandas.obtener(comanda_id, tenant_id)
        if comanda is None:
            raise ComandaNoEncontrada(comanda_id)
        comanda.cerrar()
        comprobante = await self._facturacion.emitir(SolicitudComprobante.desde(comanda))
        comanda.marcar_facturada(comprobante)
        await self._comandas.guardar(comanda)
        return comprobante
```

> Nótese: este caso de uso **no cambia** si AFIP es Build o Buy, ni si la DB es Postgres u otra. Esa es la póliza de seguro.

---

## 5. Capa 3 — Infrastructure (adapters)

**Repositorio** (implementa el port, usa ORM + mapper):

```python
# infrastructure/persistence/comanda_repo.py
from app.domain.comanda.repository import ComandaRepository
from app.domain.comanda.entities import Comanda
from app.infrastructure.persistence.models import ComandaORM
from app.infrastructure.persistence.mappers import a_dominio, a_orm

class SqlAlchemyComandaRepository(ComandaRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def obtener(self, comanda_id: str, tenant_id: str) -> Comanda | None:
        async with self._session_factory() as s:
            row = await s.get(ComandaORM, comanda_id)
            if row is None or row.tenant_id != tenant_id:   # filtrado por tenant SIEMPRE
                return None
            return a_dominio(row)

    async def guardar(self, comanda: Comanda) -> None:
        async with self._session_factory() as s:
            await s.merge(a_orm(comanda))
            await s.commit()
```

**Adapter AFIP (Build)** — mañana se reemplaza por `AfipMiddlewareFacturacion` sin tocar nada más:

```python
# infrastructure/afip/afip_directo.py
from app.domain.facturacion.ports import FacturacionElectronica
from app.domain.facturacion.entities import Comprobante, SolicitudComprobante

class AfipDirectoFacturacion(FacturacionElectronica):
    def __init__(self, cuit: str, cert_path: str, key_path: str):
        ...  # WSAA (cert X.509) + WSFEv1
    async def emitir(self, solicitud: SolicitudComprobante) -> Comprobante:
        ...  # pedir CAE a ARCA y devolver Comprobante
```

**Adapter Copiloto (text-to-SQL con guardrails)** — read-only, valida y muestra fuentes:

```python
# infrastructure/llm/anthropic_copiloto.py
from app.domain.copiloto.ports import CopilotoLLM

class AnthropicCopiloto(CopilotoLLM):
    def __init__(self, api_key: str, schema_permitido: dict):
        ...
    async def responder(self, pregunta: str, tenant_id: str):
        # 1) generar SQL acotado al schema permitido y al tenant_id
        # 2) ejecutar SOLO lectura; 3) validar números; 4) devolver respuesta + SQL/fuente
        ...
```

---

## 6. Capa 4 — Presentation (FastAPI fino)

Los routers **no tienen lógica de negocio**: traducen HTTP ⇄ DTO del caso de uso y delegan.

```python
# presentation/api/v1/comandas.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from app.container import Container
from app.application.comanda.cerrar_y_facturar import CerrarYFacturar
from app.presentation.deps import tenant_actual

router = APIRouter(prefix="/comandas", tags=["comandas"])

@router.post("/{comanda_id}/facturar")
@inject
async def facturar(
    comanda_id: str,
    tenant_id: str = Depends(tenant_actual),
    caso: CerrarYFacturar = Depends(Provide[Container.cerrar_y_facturar]),
):
    comp = await caso.ejecutar(comanda_id, tenant_id)
    return {"cae": comp.cae, "vencimiento": comp.vencimiento_cae}
```

---

## 7. DI con `dependency-injector` (el contenedor IoC)

```python
# container.py
from dependency_injector import containers, providers
from app.config import Settings
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.comanda_repo import SqlAlchemyComandaRepository
from app.infrastructure.afip.afip_directo import AfipDirectoFacturacion
from app.application.comanda.cerrar_y_facturar import CerrarYFacturar

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.presentation"])
    config = providers.Singleton(Settings)
    db = providers.Singleton(Database, url=config.provided.database_url)

    comanda_repository = providers.Factory(
        SqlAlchemyComandaRepository, session_factory=db.provided.session,
    )
    facturacion = providers.Singleton(
        AfipDirectoFacturacion,
        cuit=config.provided.afip_cuit,
        cert_path=config.provided.afip_cert,
        key_path=config.provided.afip_key,
    )
    cerrar_y_facturar = providers.Factory(
        CerrarYFacturar, comandas=comanda_repository, facturacion=facturacion,
    )
```

**El payoff Build→Buy:** para pasar a "Buy" sólo cambia una línea:
```python
    facturacion = providers.Singleton(AfipMiddlewareFacturacion, api_key=config.provided.afip_api_key)
```
Cero cambios en casos de uso ni dominio.

**El payoff en tests (SOLID en acción):**
```python
container.comanda_repository.override(providers.Factory(FakeComandaRepository))
container.facturacion.override(providers.Singleton(FakeFacturacion))
```

---

## 8. Multi-tenant

1. El `tenant_id` sale del JWT (o subdominio) en un middleware/dependency → se guarda en un `ContextVar`.
2. **Todos** los repos filtran por `tenant_id` (ver §5). Nunca una query sin tenant.
3. **RLS en Postgres** como red de seguridad: políticas que usan `current_setting('app.tenant_id')`, seteado por sesión.

```python
# presentation/deps.py
from contextvars import ContextVar
tenant_ctx: ContextVar[str] = ContextVar("tenant_id")

async def tenant_actual(...) -> str:
    # validar JWT, extraer tenant, set en contextvar, devolver
    ...
```

---

## 9. Manejo de errores

- El dominio lanza **excepciones de dominio** (`ComandaNoEncontrada`, etc.), sin saber de HTTP.
- `presentation/errors.py` registra handlers que las mapean a códigos HTTP (404, 409, 422...).
- Nunca devolver `HTTPException` desde un caso de uso o el dominio.

---

## 10. Testing

| Qué | Cómo | Sin |
|---|---|---|
| Dominio | unit puro | DB, red |
| Casos de uso | unit con **fakes** de los ports (override del contenedor) | DB, AFIP real |
| Adapters | integration | — (usar DB de test, AFIP **homologación**) |
| API | e2e sobre app con contenedor de test | AFIP real |

Meta de cobertura: **80%+** en dominio y casos de uso (la lógica crítica).

---

## 11. Convenciones

- **Idioma — backend 100% en inglés:** todo el código (clases, funciones, variables, **endpoints**, tablas/columnas de DB, comentarios) en inglés. La **UX va en español** (emails y textos al usuario); los errores de API devuelven `code` en inglés + `message` en español. Glosario ES→EN en `CLAUDE.md`. **Nota:** los snippets de esta guía son ilustrativos del PATRÓN/estructura — los identificadores reales se escriben en inglés según el glosario (ej. `Comanda`→`Order`, `CerrarYFacturar`→`CloseAndInvoice`).
- **Tres cosas distintas, nunca las confundas:**
  - *Entidad de dominio* (`Comanda`) — reglas de negocio.
  - *Modelo ORM* (`ComandaORM`) — mapeo a tablas.
  - *Schema Pydantic* (`ComandaResponse`) — contrato HTTP.
  - Entre ellos: **mappers** explícitos.
- **Prohibido:**
  - ❌ Lógica de negocio en routers o en modelos ORM.
  - ❌ Importar SQLAlchemy / FastAPI / `anthropic` desde `domain` o `application`.
  - ❌ Instanciar adapters a mano dentro de un caso de uso (se inyectan).
  - ❌ Queries sin filtro de `tenant_id`.
  - ❌ Un servicio externo (AFIP, LLM, pagos) sin su port.

---

## 12. Checklist antes de mergear

- [ ] ¿El dominio sigue sin importar frameworks?
- [ ] ¿El caso de uso depende de ports, no de implementaciones?
- [ ] ¿El servicio externo nuevo tiene su port + adapter + provider en el contenedor?
- [ ] ¿Hay filtro de `tenant_id` en toda query nueva?
- [ ] ¿Tests de dominio/caso de uso con fakes (sin DB)?
- [ ] ¿Router fino (sin lógica)?
