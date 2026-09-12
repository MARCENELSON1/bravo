from __future__ import annotations

from pydantic import BaseModel, Field


class ModifierOptionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_delta: int = Field(default=0, ge=0)


class ModifierGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    min_select: int = Field(default=0, ge=0)
    max_select: int = Field(default=1, ge=1)
    options: list[ModifierOptionRequest] = Field(min_length=1)


class SetModifiersRequest(BaseModel):
    groups: list[ModifierGroupRequest] = Field(default_factory=list)


class ModifierOptionResponse(BaseModel):
    id: str
    name: str
    price_delta: int


class ModifierGroupResponse(BaseModel):
    id: str
    name: str
    min_select: int
    max_select: int
    required: bool
    options: list[ModifierOptionResponse]


class ProductModifiersResponse(BaseModel):
    product_id: str
    groups: list[ModifierGroupResponse]
