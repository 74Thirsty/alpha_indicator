from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from ..config import Settings, get_settings


class ProviderStatus(StrEnum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EFileSubmission:
    provider_submission_id: str
    status: ProviderStatus
    acknowledgement: str | None = None


class EFileProvider(ABC):
    @abstractmethod
    def submit_return(self, *, filing_id: str, tax_year: int, encrypted_document_hashes: list[str]) -> EFileSubmission: ...

    @abstractmethod
    def check_status(self, provider_submission_id: str) -> ProviderStatus: ...

    @abstractmethod
    def handle_rejection(self, provider_submission_id: str, rejection_code: str) -> str: ...

    @abstractmethod
    def fetch_acknowledgement(self, provider_submission_id: str) -> str: ...


class MockEFileProvider(EFileProvider):
    def __init__(self):
        self._statuses: dict[str, ProviderStatus] = {}

    def submit_return(self, *, filing_id: str, tax_year: int, encrypted_document_hashes: list[str]) -> EFileSubmission:
        submission_id = f"mock-{filing_id}-{tax_year}"
        self._statuses[submission_id] = ProviderStatus.SUBMITTED
        return EFileSubmission(submission_id, ProviderStatus.SUBMITTED)

    def simulate(self, provider_submission_id: str, status: ProviderStatus) -> None:
        self._statuses[provider_submission_id] = status

    def check_status(self, provider_submission_id: str) -> ProviderStatus:
        return self._statuses.get(provider_submission_id, ProviderStatus.REJECTED)

    def handle_rejection(self, provider_submission_id: str, rejection_code: str) -> str:
        self._statuses[provider_submission_id] = ProviderStatus.REJECTED
        return f"mock rejection {rejection_code} recorded for correction workflow"

    def fetch_acknowledgement(self, provider_submission_id: str) -> str:
        status = self.check_status(provider_submission_id)
        return f"MOCK-ACK:{provider_submission_id}:{status.value}"


class ProductionEFileProvider(EFileProvider):
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        missing = [name for name in ("production_efile_provider_id", "production_efile_api_url", "production_efile_api_key") if not getattr(self.settings, name)]
        if missing:
            raise RuntimeError("Production e-file adapter is blocked until IRS-authorized provider credentials are configured: " + ", ".join(missing))

    def submit_return(self, *, filing_id: str, tax_year: int, encrypted_document_hashes: list[str]) -> EFileSubmission:
        raise NotImplementedError("Real IRS submission requires approved provider API mapping, official schemas, and production credentials.")

    def check_status(self, provider_submission_id: str) -> ProviderStatus:
        raise NotImplementedError("Real status checks require approved provider API mapping.")

    def handle_rejection(self, provider_submission_id: str, rejection_code: str) -> str:
        raise NotImplementedError("Real rejection handling requires approved provider API mapping.")

    def fetch_acknowledgement(self, provider_submission_id: str) -> str:
        raise NotImplementedError("Official acknowledgement retrieval requires approved provider API mapping.")
