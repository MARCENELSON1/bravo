from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    no_contactar: bool = False


class CustomerResponse(BaseModel):
    id: str
    name: str
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    no_contactar: bool = False


class CustomerHistoryResponse(BaseModel):
    customer_id: str
    currency: str
    visits: int
    total_spent: int  # minor units
    last_visit_at: str | None = None  # ISO-8601


class AssignCustomerRequest(BaseModel):
    customer_id: str | None = None  # None → desatribuir


class CustomerStatsRowResponse(BaseModel):
    customer_id: str
    name: str
    phone: str | None = None
    visits: int
    total_spent: int  # minor units
    first_visit_at: str | None = None  # ISO-8601
    last_visit_at: str | None = None  # ISO-8601


class CustomerStatsResponse(BaseModel):
    currency: str
    rows: list[CustomerStatsRowResponse]
