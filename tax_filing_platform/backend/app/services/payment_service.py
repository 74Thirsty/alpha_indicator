from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.enums import FilingStatus, UserRole
from ..models.filing import Filing
from .filing_service import FilingService


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.filing_service = FilingService(db)

    def initiate_refund(self, *, filing: Filing, admin_user_id: str, admin_role: UserRole, reason: str, super_admin_override: bool = False) -> Filing:
        return self.filing_service.update_status(
            filing=filing,
            new_status=FilingStatus.REFUNDED,
            actor_user_id=admin_user_id,
            actor_role=admin_role,
            reason=reason,
            super_admin_override=super_admin_override,
        )
