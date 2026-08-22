from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.table_session.entities import Sector
from app.domain.table_session.exceptions import SectorNotFound
from app.domain.table_session.repository import SectorRepository


class ListSectors:
    def __init__(
        self, sectors: SectorRepository, tenant_context: TenantContext
    ) -> None:
        self._sectors = sectors
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Sector]:
        self._tenant_context.set(tenant_id)
        return await self._sectors.list(tenant_id)


class CreateSector:
    def __init__(
        self, sectors: SectorRepository, tenant_context: TenantContext
    ) -> None:
        self._sectors = sectors
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        color: str | None = None,
        sort_order: int = 0,
    ) -> Sector:
        self._tenant_context.set(tenant_id)
        sector = Sector(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            color=color,
            sort_order=sort_order,
        )
        await self._sectors.add(sector)
        return sector


class UpdateSector:
    def __init__(
        self, sectors: SectorRepository, tenant_context: TenantContext
    ) -> None:
        self._sectors = sectors
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        sector_id: str,
        name: str,
        color: str | None,
        sort_order: int,
    ) -> Sector:
        self._tenant_context.set(tenant_id)
        sector = await self._sectors.get_by_id(tenant_id, sector_id)
        if sector is None:
            raise SectorNotFound()
        sector.name = name
        sector.color = color
        sector.sort_order = sort_order
        await self._sectors.save(sector)
        return sector


class DeleteSector:
    """Delete a sector. Tables that pointed to it fall back to "Sin sector" on
    the floor (the id becomes dangling but harmless — there's no FK), so a
    deletion never blocks on assignments."""

    def __init__(
        self, sectors: SectorRepository, tenant_context: TenantContext
    ) -> None:
        self._sectors = sectors
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, sector_id: str) -> None:
        self._tenant_context.set(tenant_id)
        sector = await self._sectors.get_by_id(tenant_id, sector_id)
        if sector is None:
            raise SectorNotFound()
        await self._sectors.delete(tenant_id, sector_id)
