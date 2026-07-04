from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.ports import NarratedInsight


class AdvisorSettingsRepository(ABC):
    """Port for the per-tenant cost profile (1:1). Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> AdvisorSettings | None: ...

    @abstractmethod
    async def save(self, settings: AdvisorSettings) -> None: ...


@dataclass(frozen=True)
class CachedDiagnostics:
    """Una tanda de diagnósticos ya narrados (insights + summary) cacheados con su
    momento de generación. Se sirve instantáneo mientras no cambie la data."""

    insights: list[NarratedInsight]
    summary: str | None
    generated_at: datetime


class AdvisorDiagnosticsCache(ABC):
    """Caché de los textos narrados (capa 3 del doc): evita re-llamar al LLM por
    cada apertura. Clave = ``fingerprint`` (hash determinístico de los insights +
    proveedor). Scopeado por ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str, fingerprint: str) -> CachedDiagnostics | None: ...

    @abstractmethod
    async def put(
        self, tenant_id: str, fingerprint: str, diagnostics: CachedDiagnostics
    ) -> None: ...

    @abstractmethod
    async def purge(self, tenant_id: str) -> int:
        """Borra todo lo cacheado del tenant (rebuild manual). Devuelve cuántas
        entradas se borraron; el próximo request regenera."""
