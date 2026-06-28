from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.order.value_objects import Station


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_amount: int = Field(ge=0)  # minor units (e.g. centavos)
    category: str | None = Field(default=None, max_length=60)
    # Where it's prepared — defaults to the kitchen; set BAR for drinks/coffee.
    station: Station = Station.KITCHEN


class CreateProductResponse(BaseModel):
    product_id: str


class ProductResponse(BaseModel):
    id: str
    name: str
    price_amount: int
    currency: str
    category: str | None
    station: str
    active: bool
