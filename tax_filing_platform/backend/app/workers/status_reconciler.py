from __future__ import annotations

from sqlalchemy.orm import Session

from ..integrations.irs_efile_provider import EFileProvider, ProviderStatus
from ..models.enums import FilingStatus, UserRole
from ..models.filing import Filing
from ..services.filing_service import FilingService


class StatusReconciler:
    def __init__(self, db: Session, provider: EFileProvider):
        self.db = db
        self.provider = provider

    def reconcile_filing(self, filing: Filing, operator_user_id: str) -> Filing:
        if not filing.provider_submission_id:
            return filing
        provider_status = self.provider.check_status(filing.provider_submission_id)
        if provider_status == ProviderStatus.ACCEPTED and filing.status == FilingStatus.FILED:
            filing.provider_acknowledgement = self.provider.fetch_acknowledgement(filing.provider_submission_id)
            return FilingService(self.db).update_status(filing=filing, new_status=FilingStatus.ACCEPTED, actor_user_id=operator_user_id, actor_role=UserRole.OPERATOR, reason="provider accepted return")
        if provider_status == ProviderStatus.REJECTED and filing.status == FilingStatus.FILED:
            filing.provider_acknowledgement = self.provider.fetch_acknowledgement(filing.provider_submission_id)
            return FilingService(self.db).update_status(filing=filing, new_status=FilingStatus.REJECTED, actor_user_id=operator_user_id, actor_role=UserRole.OPERATOR, reason="provider rejected return")
        return filing
