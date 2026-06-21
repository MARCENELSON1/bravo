from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.reservation.value_objects import ServiceTurn


class CreateReservationRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    party_size: int = Field(gt=0)
    reserved_at: datetime
    turn: ServiceTurn
    customer_phone: str | None = Field(default=None, max_length=40)
    table_id: str | None = None
    note: str | None = Field(default=None, max_length=255)


class UpdateReservationRequest(BaseModel):
    party_size: int = Field(gt=0)
    reserved_at: datetime
    turn: ServiceTurn
    table_id: str | None = None


class ReservationResponse(BaseModel):
    id: str
    customer_name: str
    customer_phone: str | None
    party_size: int
    reserved_at: datetime
    turn: str
    table_id: str | None
    status: str
    note: str | None
    created_at: datetime | None


class CreateReservationResponse(BaseModel):
    reservation_id: str
