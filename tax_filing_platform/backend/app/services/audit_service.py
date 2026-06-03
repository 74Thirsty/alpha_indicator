from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.audit_log import AdminAction, AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, *, actor_user_id: str | None, action: str, target_type: str, target_id: str, metadata: dict | None = None) -> AuditLog:
        row = AuditLog(actor_user_id=actor_user_id, action=action, target_type=target_type, target_id=target_id, metadata_json=metadata or {})
        self.db.add(row)
        return row

    def admin_action(self, *, admin_user_id: str, action: str, filing_id: str | None, metadata: dict | None = None) -> AdminAction:
        row = AdminAction(admin_user_id=admin_user_id, action=action, filing_id=filing_id, metadata_json=metadata or {})
        self.db.add(row)
        self.log(actor_user_id=admin_user_id, action=action, target_type="filing", target_id=filing_id or "system", metadata=metadata)
        return row
