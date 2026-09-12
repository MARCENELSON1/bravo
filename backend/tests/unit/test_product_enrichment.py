from __future__ import annotations

import pytest

from app.application.product.use_cases import SetProductAvailability
from app.domain.product.entities import Product
from app.domain.product.exceptions import ProductNotFound
from app.domain.shared.money import Money
from tests.fakes import FakeTenantContext


class _FakeProducts:
    def __init__(self, product: Product | None = None) -> None:
        self._by_id = {product.id: product} if product else {}
        self.saved: list[Product] = []

    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        return self._by_id.get(product_id)

    async def save(self, product: Product) -> None:
        self.saved.append(product)


def _product(**kw: object) -> Product:
    return Product(id="p1", tenant_id="t1", name="Pizza", price=Money(1000, "ARS"), **kw)  # type: ignore[arg-type]


def test_entity_enrichment_defaults_are_parity() -> None:
    p = _product()
    assert p.image_url is None
    assert p.description is None
    assert p.available_today is True


async def test_set_availability_toggles_only_that_flag() -> None:
    p = _product()
    repo = _FakeProducts(p)
    uc = SetProductAvailability(products=repo, tenant_context=FakeTenantContext())  # type: ignore[arg-type]

    out = await uc.execute(tenant_id="t1", product_id="p1", available_today=False)

    assert out.available_today is False
    assert out.active is True  # '86'd' never touches the permanent delisting
    assert repo.saved == [p]


async def test_set_availability_missing_product_raises() -> None:
    uc = SetProductAvailability(
        products=_FakeProducts(),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
    )
    with pytest.raises(ProductNotFound):
        await uc.execute(tenant_id="t1", product_id="nope", available_today=True)
