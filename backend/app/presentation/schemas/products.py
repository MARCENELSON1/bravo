from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.order.value_objects import Station


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    price_amount: int = Field(ge=0)  # minor units (e.g. centavos)
    category: str | None = Field(default=None, max_length=60)
    # Where it's prepared — defaults to the kitchen; set BAR for drinks/coffee.
    station: Station = Station.KITCHEN
    # QR menu enrichment (Carta QR F2). Optional; a photo URL + a short description.
    image_url: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def _real_name(cls, value: str) -> str:
        # Reject blank/garbage names: require min length and one alphanumeric char.
        name = value.strip()
        if len(name) < 2 or not any(char.isalnum() for char in name):
            raise ValueError("invalid product name")
        return name


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
    image_url: str | None = None
    description: str | None = None
    available_today: bool = True
    # Tiempo de servicio: IMMEDIATE | STARTER | MAIN | DESSERT.
    course: str = "MAIN"


class SetAvailabilityRequest(BaseModel):
    available_today: bool


class SetCourseRequest(BaseModel):
    course: Literal["IMMEDIATE", "STARTER", "MAIN", "DESSERT"]


# --- Productos v2 Tanda B: precios vs inflación + histórico + rotación --------


class UpdateProductPriceRequest(BaseModel):
    price_amount: int = Field(ge=0)  # nuevo precio en minor units


class PricingRowResponse(BaseModel):
    product_id: str
    product_name: str
    current_price_amount: int
    suggested_price_amount: int
    gap_amount: int
    gap_bps: int
    days_since_change: int
    lagging: bool


class PricingInsightsResponse(BaseModel):
    currency: str
    monthly_inflation_bps: int
    configured: bool
    rows: list[PricingRowResponse]


class PriceChangeResponse(BaseModel):
    changed_at: str
    old_price_amount: int | None
    new_price_amount: int


class ProductPriceHistoryResponse(BaseModel):
    product_id: str
    currency: str
    changes: list[PriceChangeResponse]


class WeekdayRotationResponse(BaseModel):
    weekday: int  # 0 = Lunes .. 6 = Domingo
    units: int
    sales_amount: int
    top_product_name: str | None


class ProductRotationResponse(BaseModel):
    currency: str
    rows: list[WeekdayRotationResponse]
