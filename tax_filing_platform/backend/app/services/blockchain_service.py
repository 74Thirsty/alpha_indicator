from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.audit_log import BlockchainEvent
from ..models.payment import Payment
from ..schemas.payment import BlockchainWebhook
from .audit_service import AuditService


class BlockchainService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def ingest_paid_event(self, payload: BlockchainWebhook) -> BlockchainEvent:
        existing = self.db.query(BlockchainEvent).filter(BlockchainEvent.tx_hash == payload.tx_hash, BlockchainEvent.log_index == payload.log_index).first()
        if existing:
            return existing
        event = BlockchainEvent(tx_hash=payload.tx_hash, log_index=payload.log_index, event_name="FilingPaid", payload=payload.model_dump())
        self.db.add(event)
        self.audit.log(actor_user_id=None, action="blockchain.event_ingested", target_type="order", target_id=str(payload.order_id), metadata=payload.model_dump())
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_payment_by_order(self, order_id: int) -> Payment | None:
        return self.db.query(Payment).filter(Payment.contract_order_id == order_id).first()

    def reconcile(self) -> dict[str, int]:
        return {"events_checked": self.db.query(BlockchainEvent).count(), "payments_matched": self.db.query(Payment).count()}
