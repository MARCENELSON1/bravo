from __future__ import annotations

from app.application.order.self_order import (
    GetSelfOrderSettings,
    UpdateSelfOrderSettings,
)
from app.domain.order.settings import SelfOrderSettings, SelfOrderSettingsRepository
from tests.fakes import FakeTenantContext


class _FakeRepo(SelfOrderSettingsRepository):
    def __init__(self, current: SelfOrderSettings | None = None) -> None:
        self._current = current or SelfOrderSettings()

    async def get(self, tenant_id: str) -> SelfOrderSettings:
        return self._current

    async def update(self, tenant_id: str, settings: SelfOrderSettings) -> None:
        self._current = settings


def test_defaults_are_disabled_and_gated() -> None:
    s = SelfOrderSettings()
    assert s.enabled is False
    assert s.requires_confirmation is True


async def test_get_returns_current() -> None:
    repo = _FakeRepo(SelfOrderSettings(enabled=True, requires_confirmation=False))
    uc = GetSelfOrderSettings(settings=repo, tenant_context=FakeTenantContext())
    out = await uc.execute(tenant_id="t1")
    assert out.enabled is True
    assert out.requires_confirmation is False


async def test_update_persists() -> None:
    repo = _FakeRepo()
    uc = UpdateSelfOrderSettings(settings=repo, tenant_context=FakeTenantContext())
    out = await uc.execute(tenant_id="t1", enabled=True, requires_confirmation=False)
    assert out == SelfOrderSettings(enabled=True, requires_confirmation=False)
    assert await repo.get("t1") == out
