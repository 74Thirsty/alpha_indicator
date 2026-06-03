from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import FilingStatus


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    data_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    status: Mapped[FilingStatus] = mapped_column(Enum(FilingStatus), default=FilingStatus.PAID, nullable=False)
    contract_order_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    signature_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_submission_id: Mapped[str | None] = mapped_column(String(128))
    provider_acknowledgement: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="filings")
    documents = relationship("Document", back_populates="filing")
    payments = relationship("Payment", back_populates="filing")
