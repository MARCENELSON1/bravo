from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateProductResult:
    product_id: str
