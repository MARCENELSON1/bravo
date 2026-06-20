from __future__ import annotations

from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_amount: int = Field(ge=0)  # minor units (e.g. centavos)
    category: str | None = Field(default=None, max_length=60)


class CreateProductResponse(BaseModel):
    product_id: str


class ProductResponse(BaseModel):
    id: str
    name: str
    price_amount: int
    currency: str
    category: str | None
    active: bool
