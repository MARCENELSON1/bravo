"""Application port the payment settle depends on, so the payment use case can
trigger stock consumption without importing the inventory implementation
(dependencies point inward; payment ← interface, not ← inventory adapter)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class InventoryConsumer(ABC):
    """Discount an order's recipes from stock once it becomes PAID. Must be
    idempotent: calling it twice for the same order discounts stock once."""

    @abstractmethod
    async def consume_for_order(self, tenant_id: str, order_id: str) -> None: ...
