from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.enums import FilingStatus, UserRole
from ..models.filing import Filing
from ..schemas.filing import FilingCreate
from .audit_service import AuditService

ALLOWED_TRANSITIONS: set[tuple[FilingStatus, FilingStatus]] = {
    (FilingStatus.PAID, FilingStatus.DOCUMENTS_RECEIVED),
    (FilingStatus.DOCUMENTS_RECEIVED, FilingStatus.IN_REVIEW),
    (FilingStatus.IN_REVIEW, FilingStatus.READY_FOR_SIGNATURE),
    (FilingStatus.READY_FOR_SIGNATURE, FilingStatus.FILED),
    (FilingStatus.FILED, FilingStatus.ACCEPTED),
    (FilingStatus.FILED, FilingStatus.REJECTED),
    (FilingStatus.REJECTED, FilingStatus.IN_REVIEW),
    (FilingStatus.PAID, FilingStatus.REFUNDED),
    (FilingStatus.DOCUMENTS_RECEIVED, FilingStatus.REFUNDED),
    (FilingStatus.IN_REVIEW, FilingStatus.REFUNDED),
}


class InvalidStatusTransition(ValueError):
    pass


class FilingService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def create(self, user_id: str, payload: FilingCreate) -> Filing:
        filing = Filing(user_id=user_id, tax_year=payload.tax_year, data_hash=payload.data_hash, status=FilingStatus.PAID)
        self.db.add(filing)
        self.db.flush()
        self.audit.log(actor_user_id=user_id, action="filing.created", target_type="filing", target_id=filing.id, metadata={"tax_year": payload.tax_year})
        self.db.commit()
        self.db.refresh(filing)
        return filing

    def update_status(self, *, filing: Filing, new_status: FilingStatus, actor_user_id: str, actor_role: UserRole, reason: str, super_admin_override: bool = False) -> Filing:
        if (filing.status, new_status) not in ALLOWED_TRANSITIONS:
            allowed_override = actor_role == UserRole.SUPER_ADMIN and super_admin_override and filing.status == FilingStatus.ACCEPTED and new_status == FilingStatus.REFUNDED
            if not allowed_override:
                raise InvalidStatusTransition(f"{filing.status} -> {new_status} is not allowed")
        old = filing.status
        filing.status = new_status
        self.audit.admin_action(admin_user_id=actor_user_id, action="filing.status_updated", filing_id=filing.id, metadata={"old": old.value, "new": new_status.value, "reason": reason})
        self.db.commit()
        self.db.refresh(filing)
        return filing

    def signature_consent(self, *, filing: Filing, user_id: str) -> Filing:
        filing.signature_consent_at = datetime.now(timezone.utc)
        self.audit.log(actor_user_id=user_id, action="filing.signature_consent", target_type="filing", target_id=filing.id)
        self.db.commit()
        self.db.refresh(filing)
        return filing
