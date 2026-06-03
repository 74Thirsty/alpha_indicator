from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import FilingStatus


class FilingCreate(BaseModel):
    tax_year: int = Field(ge=2000, le=2100)
    data_hash: str = Field(pattern=r"^0x[a-fA-F0-9]{64}$")


class FilingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tax_year: int
    data_hash: str
    status: FilingStatus
    contract_order_id: int | None
    created_at: datetime


class StatusUpdate(BaseModel):
    status: FilingStatus
    reason: str = Field(min_length=3, max_length=500)
    super_admin_override: bool = False
