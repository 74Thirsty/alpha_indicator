from __future__ import annotations

from sqlalchemy.orm import Session

from ..integrations.irs_efile_provider import EFileProvider
from ..models.enums import FilingStatus, UserRole
from ..models.filing import Filing
from ..services.filing_service import FilingService


class FilingProcessor:
    def __init__(self, db: Session, provider: EFileProvider):
        self.db = db
        self.provider = provider

    def submit_ready_filing(self, filing: Filing, operator_user_id: str) -> Filing:
        if filing.status != FilingStatus.READY_FOR_SIGNATURE or filing.signature_consent_at is None:
            raise ValueError("filing is not ready for provider submission")
        submission = self.provider.submit_return(filing_id=filing.id, tax_year=filing.tax_year, encrypted_document_hashes=[doc.sha256 for doc in filing.documents])
        filing.provider_submission_id = submission.provider_submission_id
        filing.provider_acknowledgement = submission.acknowledgement
        return FilingService(self.db).update_status(filing=filing, new_status=FilingStatus.FILED, actor_user_id=operator_user_id, actor_role=UserRole.OPERATOR, reason="submitted through configured e-file provider")
