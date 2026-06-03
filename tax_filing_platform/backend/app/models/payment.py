from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filing_id: Mapped[str] = mapped_column(ForeignKey("filings.id"), nullable=False, index=True)
    contract_order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_wallet: Mapped[str] = mapped_column(String(42), nullable=False)
    amount_wei: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(66), unique=True, nullable=False)
    refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    filing = relationship("Filing", back_populates="payments")
