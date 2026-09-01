from __future__ import annotations

from pydantic import BaseModel


class PublicMenuItemResponse(BaseModel):
    id: str
    name: str
    price_amount: int
    image_url: str | None = None
    description: str | None = None
    available_today: bool = True


class PublicMenuCategoryResponse(BaseModel):
    name: str | None
    items: list[PublicMenuItemResponse]


class PublicMenuResponse(BaseModel):
    tenant_name: str
    currency: str
    locale: str
    categories: list[PublicMenuCategoryResponse]


class IssueTableQrResponse(BaseModel):
    token: str
    url: str


class TableCallRequest(BaseModel):
    token: str


class TableCallResponse(BaseModel):
    status: str = "ok"
