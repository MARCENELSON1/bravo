from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.invoice.value_objects import DocType, FiscalCondition


class IssueInvoiceRequest(BaseModel):
    doc_type: DocType = DocType.CONSUMIDOR_FINAL
    doc_number: str = Field(default="0", max_length=20)


class InvoiceResponse(BaseModel):
    id: str
    type: str
    point_of_sale: int
    number: int | None
    doc_type: str
    doc_number: str
    net: int  # minor units
    vat: int
    total: int
    currency: str
    status: str
    cae: str | None
    cae_expiration: str | None  # ISO date
    order_id: str | None
    rejection: str | None


class AfipConnectRequest(BaseModel):
    cuit: str = Field(max_length=13)
    certificate: str
    private_key: str
    point_of_sale: int = Field(ge=1)
    fiscal_condition: FiscalCondition


class AfipConnectionResponse(BaseModel):
    connected: bool
    cuit: str | None = None
    point_of_sale: int | None = None
    fiscal_condition: str | None = None
    live_mode: bool = False
