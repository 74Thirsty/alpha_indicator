from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlockchainWebhook(BaseModel):
    tx_hash: str = Field(pattern=r"^0x[a-fA-F0-9]{64}$")
    log_index: int = Field(ge=0)
    order_id: int = Field(gt=0)
    wallet_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
    amount_wei: int = Field(gt=0)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_order_id: int
    amount_wei: int
    tx_hash: str
    refunded: bool
    created_at: datetime
