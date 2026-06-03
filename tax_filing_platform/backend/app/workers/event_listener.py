from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..schemas.payment import BlockchainWebhook
from ..services.blockchain_service import BlockchainService

logger = logging.getLogger(__name__)


@dataclass
class EventListener:
    db: Session
    poll_seconds: float = 5.0

    def handle_paid_event(self, payload: BlockchainWebhook) -> str:
        event = BlockchainService(self.db).ingest_paid_event(payload)
        logger.info("ingested blockchain event", extra={"event_id": event.id, "tx_hash": payload.tx_hash})
        return event.id

    def run_forever(self) -> None:
        while True:
            logger.info("event listener heartbeat")
            time.sleep(self.poll_seconds)
